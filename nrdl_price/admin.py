from django.contrib import admin
from .models import TC1, TC2, TC3, TC4, Company, Molecule, Subject, Negotiation


class TC1Admin(admin.ModelAdmin):
    class Meta:
        model = TC1

    search_fields = [
        "code",
        "name_cn",
        "name_en",
    ]
    

class TC2Admin(admin.ModelAdmin):
    class Meta:
        model = TC2

    search_fields = [
        "code",
        "name_cn",
        "name_en",
        "tc1__name_cn",
        "tc1__name_en"
    ]
    
class TC3Admin(admin.ModelAdmin):
    class Meta:
        model = TC3

    search_fields = [
        "code",
        "name_cn",
        "name_en",
        "tc2__name_cn",
        "tc2__name_en"
    ]
    

class TC4Admin(admin.ModelAdmin):
    class Meta:
        model = TC4

    search_fields = [
        "code",
        "name_cn",
        "name_en",
        "tc3__name_cn",
        "tc3__name_en"
    ]

class CompanyAdmin(admin.ModelAdmin):
    class Meta:
        model = Company
    
    search_fields = [
        "full_name",
        "abbr_name"
    ]

class MoleculeAdmin(admin.ModelAdmin):
    class Meta:
        model= Molecule
    
    search_fields = [
        "name_cn",
        "name_en",
        "tc4__name_cn",
        "tc4__name_en"
        
    ]

class SubjectAdmin(admin.ModelAdmin):
    class Meta:
        model = Subject
    
    search_fields = [
        "name",
        "molecule__name_cn",
        "molecule__name_en",
        "formulation",
        "therapy_class",
        "origin_company__full_name",
        "origin_company__abbr_name",
    ]

class NegotiationAdmin(admin.ModelAdmin):
    class Meta:
        model = Negotiation
        
    search_fields = [
        "subject__name",
        "subject__molecule__name_cn",
        "subject__molecule__name_en",
        "subject__formulation",
        "subject__therapy_class",
        "subject__origin_company__full_name",
        "subject__origin_company__abbr_name",
        "nego_type",
        "dosage_for_price",
        "note"
    ]
    

admin.site.register(Negotiation, NegotiationAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(Molecule, MoleculeAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(TC1, TC1Admin)
admin.site.register(TC2, TC2Admin)
admin.site.register(TC3, TC3Admin)
admin.site.register(TC4, TC4Admin)