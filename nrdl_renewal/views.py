from django.shortcuts import render


def index(request):
    return render(request, "nrdl_renewal/general_catalog.html")


def general_catalog(request):
    context = request.POST.dict()
    print(context)

    if (
        context.get("select_exclusive") == "非独家品种"
        or context.get("select_nonchange") == "2"
        or context.get("select_continuous") == "8"
    ):
        context["main_result"] = "纳入常规目录管理"
        context["price_cut"] = "0%"
        context["general_catalog"] = "纳入"
        return render(request, "nrdl_renewal/result.html", context=context)
    else:
        context["general_catalog"] = "不纳入"
        return render(request, "nrdl_renewal/if_simple.html", context=context)


def if_simple(request):
    context = request.POST.dict()
    print(context)

    if (
        context.get("select_200") == "超支200%以上"
        or context.get("select_uplift") == "预期增幅超过100%"
        or context.get("select_env") == "市场环境发生重大变化"
    ):
        context["main_result"] = "不能简易续约，重新谈判"
        context["price_cut"] = "25%以上"
        context["general_catalog"] = "不纳入"
        context["if_simple"] = "重新谈判"
        return render(request, "nrdl_renewal/result.html", context=context)
    else:
        context["general_catalog"] = "不纳入"
        context["if_simple"] = "简易续约"
        return render(request, "nrdl_renewal/price_cut.html", context=context)


def price_cut(request):
    context = request.POST.dict()
    print(context)

    annual = context.get("select_annual")
    ratio = context.get("select_ratio")
    annual_new = context.get("select_annual_new")
    ratio_new = context.get("select_ratio_new")
    continuous = int(context.get("select_continuous"))

    # 计算a值
    if annual == "<=2亿元":
        if ratio == "<=110%":
            a = 0
        elif ratio == "110%-140%":
            a = 0.05
        elif ratio == "140%-170%":
            a = 0.1
        elif ratio == "170%-200%":
            a = 0.15
    elif annual == "2-10亿元":
        if ratio == "<=110%":
            a = 0
        elif ratio == "110%-140%":
            a = 0.07
        elif ratio == "140%-170%":
            a = 0.12
        elif ratio == "170%-200%":
            a = 0.17
    elif annual == "10-20亿元":
        if ratio == "<=110%":
            a = 0
        elif ratio == "110%-140%":
            a = 0.09
        elif ratio == "140%-170%":
            a = 0.14
        elif ratio == "170%-200%":
            a = 0.19
    elif annual == "20-40亿元":
        if ratio == "<=110%":
            a = 0
        elif ratio == "110%-140%":
            a = 0.11
        elif ratio == "140%-170%":
            a = 0.16
        elif ratio == "170%-200%":
            a = 0.21
    elif annual == ">40亿元":
        if ratio == "<=110%":
            a = 0
        elif ratio == "110%-140%":
            a = 0.15
        elif ratio == "140%-170%":
            a = 0.2
        elif ratio == "170%-200%":
            a = 0.25

    # 计算b值
    if annual_new == "0":
        b = 0
    elif annual_new == "<=2亿元":
        if ratio_new == "<=10%":
            b = 0
        elif ratio_new == "10%-40%":
            b = 0.05
        elif ratio_new == "40%-70%":
            b = 0.1
        elif ratio_new == "70%-100%":
            b = 0.15
    elif annual_new == "2-10亿元":
        if ratio_new == "<=10%":
            b = 0
        elif ratio_new == "10%-40%":
            b = 0.07
        elif ratio_new == "40%-70%":
            b = 0.12
        elif ratio_new == "70%-100%":
            b = 0.17
    elif annual_new == "10-20亿元":
        if ratio_new == "<=10%":
            b = 0
        elif ratio_new == "10%-40%":
            b = 0.09
        elif ratio_new == "40%-70%":
            b = 0.14
        elif ratio_new == "70%-100%":
            b = 0.19
    elif annual_new == "20-40亿元":
        if ratio_new == "<=10%":
            b = 0
        elif ratio_new == "10%-40%":
            b = 0.11
        elif ratio_new == "40%-70%":
            b = 0.16
        elif ratio_new == "70%-100%":
            b = 0.21
    elif annual_new == ">40亿元":
        if ratio_new == "<=10%":
            b = 0
        elif ratio_new == "10%-40%":
            b = 0.15
        elif ratio_new == "40%-70%":
            b = 0.2
        elif ratio_new == "70%-100%":
            b = 0.25

    if continuous < 4:
        index = 1
    else:
        index = 0.5

    price_cut = "{:.1f}".format((1 - (1 - a) * (1 - b)) * index * 100)
    print(a, b, index, price_cut)

    context["a"] = a
    context["b"] = b
    context["index"] = index
    context["main_result"] = "简易续约"
    context["price_cut"] = f"{price_cut}%"
    context["general_catalog"] = "不纳入"
    context["if_simple"] = "简易续约"
    return render(request, "nrdl_renewal/result.html", context=context)
