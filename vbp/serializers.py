from .models import *
from rest_framework import serializers


class TenderSerializer(serializers.ModelSerializer):
    tender_period = serializers.ReadOnlyField()
    tender_end = serializers.ReadOnlyField()
    proc_percentage = serializers.ReadOnlyField()
    winner_num = serializers.ReadOnlyField()
    amount_contract = serializers.ReadOnlyField()

    class Meta:
        model = Tender
        fields = "__all__"


class BidSerializer(serializers.ModelSerializer):

    class Meta:
        model = Bid
        fields = "__all__"
