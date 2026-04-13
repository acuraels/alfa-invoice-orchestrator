from decimal import Decimal

from rest_framework import serializers


class TransactionPayloadSerializer(serializers.Serializer):
    transactionId = serializers.CharField(required=False, allow_blank=True, max_length=128)
    drf = serializers.CharField(max_length=64)
    type = serializers.ChoiceField(choices=["INCOME", "VAT"])
    counterpartyId = serializers.IntegerField(min_value=1)
    departmentId = serializers.IntegerField(min_value=1)
    date = serializers.DateField()
    productName = serializers.CharField(required=False, allow_blank=True, max_length=255)
    unitMeasure = serializers.CharField(required=False, allow_blank=True, max_length=32)
    quantity = serializers.DecimalField(required=False, max_digits=16, decimal_places=4)
    unitPrice = serializers.DecimalField(required=False, max_digits=16, decimal_places=4)
    vatRate = serializers.DecimalField(max_digits=6, decimal_places=4)
    vatAmount = serializers.DecimalField(required=False, max_digits=16, decimal_places=4)

    def validate(self, attrs):
        tx_type = attrs["type"]

        if tx_type == "INCOME":
            required = ["productName", "unitMeasure", "quantity", "unitPrice"]
            missing = [field for field in required if field not in attrs]
            if missing:
                raise serializers.ValidationError(
                    {"missing_fields": f"INCOME requires: {', '.join(missing)}"}
                )

            if attrs.get("quantity", Decimal("0")) <= 0:
                raise serializers.ValidationError({"quantity": "quantity must be > 0"})
            if attrs.get("unitPrice", Decimal("0")) <= 0:
                raise serializers.ValidationError({"unitPrice": "unitPrice must be > 0"})

        if tx_type == "VAT" and "vatAmount" not in attrs:
            raise serializers.ValidationError({"vatAmount": "VAT requires vatAmount"})

        return attrs


class IngestTransactionsSerializer(serializers.Serializer):
    transactions = TransactionPayloadSerializer(many=True)
