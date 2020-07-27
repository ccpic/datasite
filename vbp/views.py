from .models import Tender, Volume, Bid, Company
from .serializers import TenderSerializer
from rest_framework import viewsets
from django.shortcuts import render


# class RecordViewSet(viewsets.ModelViewSet):
#     """
#     API - 带量采购记录
#     """
#     queryset = Record.objects.all().order_by('-pub_date')
#     serializer_class = RecordSerializer
#
#
# class TenderViewSet(viewsets.ModelViewSet):
#     """
#     API - 带量采购标的
#     """
#     queryset = Tender.objects.all()
#     serializer_class = TenderSerializer

def index(request):
    tenders = Tender.objects.all()

    context = {
        'tenders': tenders
    }
    return render(request, 'vbp/index.html', context)


def bid_detail(request, bid_id):
    bid = Bid.objects.get(pk=bid_id)

    context = {
        'bid': bid
    }
    return render(request, 'vbp/bid_detail.html', context)


def tender_detail(request, tender_id):
    tender = Tender.objects.get(pk=tender_id)

    context = {
        'tender': tender
    }
    return render(request, 'vbp/tender_detail.html', context)


def company_detail(request, record_id):
    company = Company.objects.get(pk=record_id)

    context = {
        'company': company
    }
    return render(request, 'vbp/bid_detail.html', context)