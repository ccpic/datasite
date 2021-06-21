from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Post
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

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
    posts = Post.objects.filter(tags__pk__in=[pk])

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
        "tag": Post.tags.filter(pk__in=[pk]).first(),
    }
    return render(request, "medical_info/posts.html", context)


@login_required
def post_detail(request, slug):
    post = Post.objects.get(url_slug=slug)

    context = {
        "post": post,
    }
    return render(request, "medical_info/post_detail.html", context)
