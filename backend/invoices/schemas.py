from decimal import Decimal

from rest_framework import serializers


class TransactionPayloadSerializer(serializers.Serializer):
    drf = serializers.CharField(max_length=64)
    type = serializers.ChoiceField(choices=["INCOME", "VAT"])
    counterpartyId = serializers.UUIDField()
    departmentId = serializers.UUIDField()
    date = serializers.DateField()
    amount = serializers.DecimalField(required=False, allow_null=True, max_digits=16, decimal_places=4)
    debitAccount = serializers.CharField(max_length=64)
    creditAccount = serializers.CharField(max_length=64)
    productName = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=255)
    unitMeasure = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=32)
    quantity = serializers.DecimalField(required=False, allow_null=True, max_digits=16, decimal_places=4)
    unitPrice = serializers.DecimalField(required=False, allow_null=True, max_digits=16, decimal_places=4)
    vatRate = serializers.DecimalField(required=False, allow_null=True, max_digits=6, decimal_places=4)
    vatAmount = serializers.DecimalField(required=False, allow_null=True, max_digits=16, decimal_places=4)
    createdAt = serializers.DateTimeField()

    def validate(self, attrs):
        tx_type = attrs["type"]

        if tx_type == "INCOME":
            required = ["amount", "productName", "unitMeasure", "quantity", "unitPrice"]
            missing = [field for field in required if attrs.get(field) in [None, ""]]
            if missing:
                raise serializers.ValidationError(
                    {"missing_fields": f"INCOME requires: {', '.join(missing)}"}
                )

            if attrs.get("amount", Decimal("0")) <= 0:
                raise serializers.ValidationError({"amount": "amount must be > 0"})
            if attrs.get("quantity", Decimal("0")) <= 0:
                raise serializers.ValidationError({"quantity": "quantity must be > 0"})
            if attrs.get("unitPrice", Decimal("0")) <= 0:
                raise serializers.ValidationError({"unitPrice": "unitPrice must be > 0"})
            if attrs.get("vatRate") is not None:
                raise serializers.ValidationError({"vatRate": "INCOME expects vatRate = null"})
            if attrs.get("vatAmount") is not None:
                raise serializers.ValidationError({"vatAmount": "INCOME expects vatAmount = null"})

        if tx_type == "VAT":
            if attrs.get("vatRate") is None:
                raise serializers.ValidationError({"vatRate": "VAT requires vatRate"})
            if attrs.get("vatAmount") is None:
                raise serializers.ValidationError({"vatAmount": "VAT requires vatAmount"})
            if attrs.get("amount") is not None:
                raise serializers.ValidationError({"amount": "VAT expects amount = null"})
            if attrs.get("productName") not in [None, ""]:
                raise serializers.ValidationError({"productName": "VAT expects productName = null"})
            if attrs.get("quantity") is not None:
                raise serializers.ValidationError({"quantity": "VAT expects quantity = null"})
            if attrs.get("unitMeasure") not in [None, ""]:
                raise serializers.ValidationError({"unitMeasure": "VAT expects unitMeasure = null"})
            if attrs.get("unitPrice") is not None:
                raise serializers.ValidationError({"unitPrice": "VAT expects unitPrice = null"})

        return attrs


class IngestTransactionsSerializer(serializers.Serializer):
    transactions = TransactionPayloadSerializer(many=True)


class InvoiceListQuerySerializer(serializers.Serializer):
    tab = serializers.ChoiceField(choices=["to_process", "processed"])
    counterparty = serializers.CharField(required=False, allow_blank=True)
    dateFrom = serializers.DateField(required=False)
    dateTo = serializers.DateField(required=False)
    status = serializers.ListField(
        child=serializers.ChoiceField(
            choices=[
                "project_created",
                "validating_error",
                "invoice_created",
                "sending_error",
                "sent",
            ]
        ),
        required=False,
    )
    departmentId = serializers.ListField(child=serializers.UUIDField(), required=False)
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    size = serializers.IntegerField(required=False, min_value=1, default=20)

    def validate(self, attrs):
        date_from = attrs.get("dateFrom")
        date_to = attrs.get("dateTo")
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError({"dateFrom": "dateFrom must be <= dateTo"})
        return attrs
