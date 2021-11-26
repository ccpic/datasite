from chpa_data.templatetags.tags import highlight
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Post, Program, Nation
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q, F, Count
import Levenshtein as lev
from django.core.serializers.json import DjangoJSONEncoder
from taggit.models import Tag

DISPLAY_LENGTH = 10


def get_id_list(param):
    id_list = []
    for id in param:
        if isinstance(id, int) == int:
            id_list.append(id)
        else:
            id_list.append(int(id))

    return id_list


def get_param(params):
    kw_param = params.get("kw")  # 根据空格拆分搜索关键字

    tag_param = params.getlist("tag")  # tag可能多选，需要额外处理
    tag_id_list = get_id_list(tag_param)

    nation_param = params.getlist("nation")  # 国家参数
    nation_id_list = get_id_list(nation_param)

    prog_param = params.get("program")  # 栏目参数

    # 下面部分准备所有高亮关键字
    highlights = {}
    try:
        kw_list = kw_param.split(" ")
    except:
        kw_list = []

    for kw in kw_list:
        highlights[kw] = '<b class="highlight_kw">{}</b>'.format(kw)

    for tag_id in tag_id_list:
        tag = Tag.objects.get(pk=tag_id)
        highlights[tag.name] = '<b class="highlight_tag">{}</b>'.format(tag.name)

    context = {
        "kw": kw_param,
        "tags": tag_id_list,
        "nations": nation_id_list,
        "program": prog_param,
        "highlights": highlights,
    }

    return context


# 首页
@login_required
def posts(request):
    print(request.GET)
    param_dict = get_param(request.GET)

    # 所有医学信息
    posts = Post.objects.all()

    # 根据搜索筛选文章
    kw = param_dict["kw"]
    if kw is not None:
        kw_list = kw.split(" ")

        search_condition = (
            Q(title_cn__icontains=kw_list[0])  # 搜索文章中文名
            | Q(title_en__icontains=kw_list[0])  # 搜索文章英文名
            | Q(pub_agent__full_name__icontains=kw_list[0])  # 搜索发布平台全称
            | Q(pub_agent__abbr_name__icontains=kw_list[0])  # 搜索发布平台简称
            | Q(abstract__icontains=kw_list[0])  # 搜索摘要
            | Q(program__name__icontains=kw_list[0])  # 搜索栏目
            | Q(tags__name__icontains=kw_list[0])  # 搜索标签
        )
        for k in kw_list[1:]:
            search_condition.add(
                Q(title_cn__icontains=k)  # 搜索文章中文名
                | Q(title_en__icontains=k)  # 搜索文章英文名
                | Q(pub_agent__full_name__icontains=k)  # 搜索发布平台全称
                | Q(pub_agent__abbr_name__icontains=k)  # 搜索发布平台简称
                | Q(abstract__icontains=k)  # 搜索摘要
                | Q(program__name__icontains=k)  # 搜索栏目
                | Q(tags__name__icontains=k),  # 搜索标签
                Q.AND,
            )

        search_result = posts.filter(search_condition).distinct()

        #  下方两行代码为了克服MSSQL数据库和Django pagination在distinct(),order_by()等queryset时出现重复对象的bug
        sr_ids = [post.id for post in search_result]
        posts = Post.objects.filter(id__in=sr_ids)

    # 根据栏目筛选文章
    program = param_dict["program"]
    if program is not None:
        posts = posts.filter(program__id=program)

    # Chain filter标签在以上基础上多选筛选文章
    for id in param_dict["tags"]:
        posts = posts.filter(tags__id=id)

    # Chain filter国家在以上基础上多选筛选文章
    for id in param_dict["nations"]:
        posts = posts.filter(nation__id=id)

    paginator = Paginator(posts, DISPLAY_LENGTH)
    page = request.GET.get("page")

    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page(1)
    except EmptyPage:
        rows = paginator.page(paginator.num_pages)

    all_tags = Tag.objects.all()
    all_tags = (
        all_tags.annotate(post_count=Count("post"))
        .distinct()
        .order_by(F("post_count").desc())
    )
    print(len(all_tags))
    filter_tags = Tag.objects.filter(post__in=posts)  # 筛选出所有关联医学信息的tags
    filter_tags = (
        filter_tags.annotate(post_count=Count("post"))
        .distinct()
        .order_by(F("post_count").desc())
    )  # 统计tag关联的医学信息数并按从高到低排序
    print(len(filter_tags))
    all_nations = Nation.objects.all()
    all_nations = all_nations.annotate(post_count=Count("post")).order_by(
        F("post_count").desc()
    )
    print(len(all_nations))
    filter_nations = Nation.objects.filter(post__in=posts)  # 筛选出所有关联医学信息的tags
    filter_nations = filter_nations.annotate(post_count=Count("post")).order_by(
        F("post_count").desc()
    )  # 统计tag关联的医学信息数并按从高到低排序
    print(len(filter_nations))

    context = {
        "posts": rows,
        "num_pages": paginator.num_pages,
        "record_n": paginator.count,
        "display_length": DISPLAY_LENGTH,
        "kw": param_dict["kw"],
        "all_tags": all_tags,
        "filter_tags": filter_tags,
        "tag_selected": Tag.objects.filter(pk__in=param_dict["tags"]),
        "all_nations": all_nations,
        "filter_nations": filter_nations,
        "nation_selected": Nation.objects.filter(pk__in=param_dict["nations"]),
        "program": Program.objects.filter(pk=program).first(),
        "highlights": param_dict["highlights"],
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
        for k, v in sorted(
            d_distance.items(), key=lambda item: item[1], reverse=True
        )  # 按Levenshtein距离由高到低排序
    }

    posts_related = Post.objects.filter(
        pk__in=list(d_distance.keys())[:5]
    )  # Levenshtein距离最高的5个posts

    all_tags = Tag.objects.all()
    all_tags = all_tags.annotate(post_count=Count("post")).order_by(
        F("post_count").desc()
    )

    all_nations = Nation.objects.all()
    all_nations = all_nations.annotate(post_count=Count("post")).order_by(
        F("post_count").desc()
    )

    context = {
        "post": post,
        "posts_related": posts_related,
        "all_tags": all_tags,
        "all_nations": all_nations,
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
