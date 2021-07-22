from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Post, Program
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q, F
import Levenshtein as lev

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
def post_detail(request, pk):
    post = Post.objects.get(pk=pk)

    key = "viewed_post_%s" % post.id
    if request.session.get(key) is None:
        # 记录浏览量

        post.views = F("views") + 1
        post.save(skip_lastupdatetime=True)
        post.refresh_from_db()
        request.session[key] = True

    # 推荐相似的医学信息
    tags = list(post.tags.values_list("name", flat=True))

    d_distance = {}
    posts_oth = Post.objects.exclude(pk=pk)
    for post_oth in posts_oth:
        d_distance[post_oth.pk] = list(
            post_oth.tags.all().values_list("name", flat=True)  # 准备除本post以外的所有post的tags
        )

    for key, value in d_distance.items():
        d_distance[key] = lev.setratio(tags, value)  # 计算本post和其他任一post的Levenshtein距离

    d_distance = {
        k: v
        for k, v in sorted(d_distance.items(), key=lambda item: item[1], reverse=True) # 按Levenshtein距离由高到低排序
    }

    posts_related = Post.objects.filter(pk__in=list(d_distance.keys())[:5]) # Levenshtein距离最高的5个posts

    context = {
        "post": post,
        "posts_related": posts_related,
    }
    return render(request, "medical_info/post_detail.html", context)


@login_required
def post_mail_format(request, pk):
    post = Post.objects.get(pk=pk)
    # baseurl = request.build_absolute_uri(post.url)
    context = {
        "post": post,
    }
    return render(request, "medical_info/post_mail_format.html", context)


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
