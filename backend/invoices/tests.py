from datetime import date
from decimal import Decimal
from uuid import UUID

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from invoices.models import (
    AggregationGroup,
    Counterparty,
    Department,
    DraftInvoice,
    ExportRecord,
    FinalInvoice,
    IdempotencyRecord,
    RawTransaction,
)
from invoices.schemas import TransactionPayloadSerializer
from invoices.services import (
    build_draft_invoice,
    generate_invoice_number,
    materialize_draft_invoice,
    materialize_ready_drafts,
    process_transaction_payload,
)

DEPARTMENT_FACTORING_UUID = UUID("11111111-1111-1111-1111-111111111111")
DEPARTMENT_ACCOUNTING_UUID = UUID("22222222-2222-2222-2222-222222222222")
COUNTERPARTY_MAIN_UUID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


def make_income_payload(
    *,
    drf: str = "DRF-1",
    counterparty_id: str = str(COUNTERPARTY_MAIN_UUID),
    department_id: str = str(DEPARTMENT_FACTORING_UUID),
    date: str = "2026-04-13",
    amount: str = "200",
    quantity: str = "2",
    unit_price: str = "100",
):
    return {
        "drf": drf,
        "type": "INCOME",
        "counterpartyId": counterparty_id,
        "departmentId": department_id,
        "date": date,
        "amount": amount,
        "debitAccount": "62.01",
        "creditAccount": "90.01",
        "productName": "Service",
        "unitMeasure": "pcs",
        "quantity": quantity,
        "unitPrice": unit_price,
        "createdAt": "2026-04-13T10:00:00Z",
    }


def make_vat_payload(
    *,
    drf: str = "DRF-1",
    counterparty_id: str = str(COUNTERPARTY_MAIN_UUID),
    department_id: str = str(DEPARTMENT_FACTORING_UUID),
    date: str = "2026-04-13",
    vat_rate: str = "0.2",
    vat_amount: str = "40",
):
    return {
        "drf": drf,
        "type": "VAT",
        "counterpartyId": counterparty_id,
        "departmentId": department_id,
        "date": date,
        "debitAccount": "68.02",
        "creditAccount": "19.03",
        "vatRate": vat_rate,
        "vatAmount": vat_amount,
        "createdAt": "2026-04-13T10:01:00Z",
    }


class BaseDomainTestCase(TestCase):
    def setUp(self):
        Department.objects.create(
            id=DEPARTMENT_FACTORING_UUID,
            code="factoring",
            name="Факторинг",
            mnemonic="fct",
        )
        Department.objects.create(
            id=DEPARTMENT_ACCOUNTING_UUID,
            code="accounting",
            name="Бухучет",
            mnemonic="acc",
        )
        Counterparty.objects.create(
            id=COUNTERPARTY_MAIN_UUID,
            name="АО Альфа Поставщик",
        )


class PayloadValidationTests(BaseDomainTestCase):
    def test_payload_validation_rejects_income_without_required_fields(self):
        serializer = TransactionPayloadSerializer(
            data={
                "drf": "DRF-10",
                "type": "INCOME",
                "counterpartyId": str(COUNTERPARTY_MAIN_UUID),
                "departmentId": str(DEPARTMENT_FACTORING_UUID),
                "date": "2026-04-13",
                "debitAccount": "62.01",
                "creditAccount": "90.01",
                "createdAt": "2026-04-13T10:00:00Z",
            }
        )
        self.assertFalse(serializer.is_valid())


class AggregationTests(BaseDomainTestCase):
    def test_aggregation_by_drf_builds_single_group_and_draft(self):
        process_transaction_payload(make_income_payload())
        process_transaction_payload(make_vat_payload())

        group = AggregationGroup.objects.get(drf="DRF-1")
        self.assertEqual(group.total_count, 2)
        self.assertEqual(group.income_count, 1)
        self.assertEqual(group.vat_count, 1)
        self.assertEqual(group.status, AggregationGroup.Status.DRAFT)

        draft = DraftInvoice.objects.get(group=group)
        self.assertEqual(draft.lines.count(), 1)
        self.assertEqual(draft.status, DraftInvoice.Status.PROJECT_CREATED)


class InvoiceNumberGenerationTests(BaseDomainTestCase):
    def test_invoice_number_sequence_is_monotonic(self):
        dep = Department.objects.get(code="factoring")
        number_1 = generate_invoice_number(department=dep, date=date(2026, 4, 13))
        number_2 = generate_invoice_number(department=dep, date=date(2026, 4, 13))
        self.assertNotEqual(number_1, number_2)
        self.assertTrue(number_1.endswith("00000001"))
        self.assertTrue(number_2.endswith("00000002"))


class DraftBuildingTests(BaseDomainTestCase):
    def test_draft_building_calculates_totals(self):
        process_transaction_payload(make_income_payload())
        process_transaction_payload(make_vat_payload())
        group = AggregationGroup.objects.get(drf="DRF-1")
        draft = build_draft_invoice(group)

        self.assertEqual(draft.total_vat_amount, Decimal("40"))
        self.assertEqual(draft.total_with_vat, Decimal("240"))


class MaterializationTests(BaseDomainTestCase):
    def test_layer1_to_layer2_materialization_creates_final_invoice(self):
        process_transaction_payload(make_income_payload())
        process_transaction_payload(make_vat_payload())
        draft = DraftInvoice.objects.get(group__drf="DRF-1")

        final = materialize_draft_invoice(draft)

        self.assertIsNotNone(final)
        self.assertEqual(FinalInvoice.objects.count(), 1)
        self.assertEqual(final.lines.count(), 1)
        self.assertEqual(ExportRecord.objects.count(), 1)
        self.assertEqual(RawTransaction.objects.filter(drf="DRF-1", invoice=final).count(), 2)
        self.assertEqual(final.status, FinalInvoice.Status.INVOICE_CREATED)


class IntegrationPipelineTests(APITestCase):
    def setUp(self):
        Department.objects.create(
            id=DEPARTMENT_FACTORING_UUID,
            code="factoring",
            name="Факторинг",
            mnemonic="fct",
        )
        Department.objects.create(
            id=DEPARTMENT_ACCOUNTING_UUID,
            code="accounting",
            name="Бухучет",
            mnemonic="acc",
        )
        Counterparty.objects.create(
            id=COUNTERPARTY_MAIN_UUID,
            name="АО Альфа Поставщик",
        )

        User = get_user_model()
        self.user = User.objects.create_user(
            username="admin_test",
            email="admin@example.com",
            password="password",
            role="admin",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_authenticate(self.user)

    def test_integration_happy_path(self):
        response = self.client.post(
            "/api/v1/ingest/transactions",
            [make_income_payload(), make_vat_payload()],
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data["published"], 2)

        result = materialize_ready_drafts(limit=10)
        self.assertEqual(result["errors"], 0)
        self.assertEqual(FinalInvoice.objects.count(), 1)

    def test_integration_validation_error(self):
        response = self.client.post(
            "/api/v1/ingest/transactions",
            [
                make_income_payload(
                    drf="DRF-BAD",
                    department_id=str(DEPARTMENT_FACTORING_UUID),
                ),
                make_vat_payload(
                    drf="DRF-BAD",
                    department_id=str(DEPARTMENT_ACCOUNTING_UUID),
                ),
            ],
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        group = AggregationGroup.objects.get(drf="DRF-BAD")
        self.assertEqual(group.status, AggregationGroup.Status.VALIDATION_ERROR)

    def test_integration_duplicate_message(self):
        payload = make_income_payload(drf="DRF-DUP")
        first = self.client.post("/api/v1/ingest/transactions", [payload], format="json")
        second = self.client.post("/api/v1/ingest/transactions", [payload], format="json")

        self.assertEqual(first.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(second.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(second.data["duplicates"], 1)
        self.assertEqual(IdempotencyRecord.objects.count(), 1)

    def test_integration_retry_path(self):
        self.client.post(
            "/api/v1/ingest/transactions",
            [make_income_payload(drf="DRF-RETRY"), make_vat_payload(drf="DRF-RETRY")],
            format="json",
        )
        materialize_ready_drafts(limit=10)
        final = FinalInvoice.objects.get(draft_invoice__group__drf="DRF-RETRY")

        response = self.client.post(f"/api/v1/final-invoices/{final.id}/retry/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        final.refresh_from_db()
        self.assertEqual(final.status, FinalInvoice.Status.SENT)
        self.assertEqual(final.export_record.status, ExportRecord.Status.SENT)
