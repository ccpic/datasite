from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Post, Program
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q,F

DISPLAY_LENGTH = 10


@login_required
def index(request):

    posts = Post.objects.all()
    paginator = Paginator(posts, DISPLAY_LENGTH)
    page = request.GET.get("page")

    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page(1)
    except EmptyPage:
        rows = paginator.page(paginator.num_pages)

    context = {
        "posts": rows,
        "num_pages": paginator.num_pages,
        "record_n": paginator.count,
        "display_length": DISPLAY_LENGTH,
    }
    return render(request, "medical_info/posts.html", context)


@login_required
def tagged(request, pk):
    posts = Post.objects.filter(tags__pk=pk)
    paginator = Paginator(posts, DISPLAY_LENGTH)
    page = request.GET.get("page")

    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page(1)
    except EmptyPage:
        rows = paginator.page(paginator.num_pages)

    context = {
        "posts": rows,
        "num_pages": paginator.num_pages,
        "record_n": paginator.count,
        "display_length": DISPLAY_LENGTH,
        "tag": Post.tags.filter(pk=pk).first(),
    }
    return render(request, "medical_info/posts.html", context)


@login_required
def program(request, pk):
    posts = Post.objects.filter(program__pk=pk)
    paginator = Paginator(posts, DISPLAY_LENGTH)
    page = request.GET.get("page")

    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page(1)
    except EmptyPage:
        rows = paginator.page(paginator.num_pages)

    context = {
        "posts": rows,
        "num_pages": paginator.num_pages,
        "record_n": paginator.count,
        "display_length": DISPLAY_LENGTH,
        "program": Program.objects.get(pk=pk),
    }
    return render(request, "medical_info/posts.html", context)


@login_required
def post_detail(request, slug):
    post = Post.objects.get(url_slug=slug)
    post.views = F("views") + 1
    post.save()
    post.refresh_from_db()
    context = {
        "post": post,
    }
    return render(request, "medical_info/post_detail.html", context)


@login_required
def search(request):
    print(request.GET)
    kw = request.GET.get("kw")
    search_result = Post.objects.filter(
        Q(title_cn__icontains=kw)  # 搜索文章中文名
        | Q(title_en__icontains=kw)  # 搜索文章英文名
        | Q(pub_agent__full_name__icontains=kw)  # 搜索发布平台全称
        | Q(pub_agent__abbr_name__icontains=kw)  # 搜索发布平台简称
        | Q(abstract__icontains=kw)  # 搜索摘要
        | Q(program__name__icontains=kw)  # 搜索栏目
        | Q(tags__name__icontains=kw)  # 搜索标签
    ).distinct()

    #  下方两行代码为了克服MSSQL数据库和Django pagination在distinc(),order_by()等queryset时出现重复对象的bug
    sr_ids = [post.id for post in search_result]
    search_result2 = Post.objects.filter(id__in=sr_ids)

    paginator = Paginator(
        search_result2, DISPLAY_LENGTH
    )  #  为了克服pagination bug这里的参数时search_result2
    page = request.GET.get("page")

    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page(1)
    except EmptyPage:
        rows = paginator.page(paginator.num_pages)

    context = {
        "posts": rows,
        "num_pages": paginator.num_pages,
        "record_n": paginator.count,
        "display_length": DISPLAY_LENGTH,
        "kw": kw,
    }

    return render(request, "medical_info/posts.html", context)
