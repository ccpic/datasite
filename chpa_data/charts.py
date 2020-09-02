from pyecharts.charts import Line, Pie, Bar, Geo, Scatter
from pyecharts import options as opts
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.font_manager as fm
from matplotlib.ticker import FuncFormatter
from adjustText import adjust_text
from io import BytesIO
import base64
import scipy.stats as stats
import squarify

myfont = fm.FontProperties(fname="C:/Windows/Fonts/msyh.ttc")


# Squarify 矩形Treemap
def treemap(sizes, diff, labels, x=0, y=0, width=1, height=1, title=None):
    # 准备画布
    fig, ax = plt.subplots(1, figsize=(15, 15 * height / width))
    ax.set_xlim(x, width)
    ax.set_ylim(y, height)

    # 创造和同比净增长关联的颜色方案
    min_diff = min(diff)
    max_diff = max(diff)
    if min_diff > 0:
        cmap = mpl.cm.Blues
        norm = mpl.colors.Normalize(vmin=min_diff, vmax=max_diff)
    elif max_diff < 0:
        cmap = mpl.cm.Reds
        norm = mpl.colors.Normalize(vmin=min_diff, vmax=max_diff)
    else:
        cmap = mpl.cm.bwr_r
        norm = mpl.colors.TwoSlopeNorm(vmin=min_diff, vcenter=0, vmax=max_diff)  # 强制0为中点的正太分布渐变色

    colors = [cmap(norm(value)) for value in diff]

    # 使用Squarify原生方法画图
    # ax = squarify.plot(sizes=sizes,
    #               label=labels[:label_limit],
    #               ax=ax,
    #               bar_kwargs=dict(linewidth=1, edgecolor="#222222"),
    #               text_kwargs={'fontname': 'SimHei',
    #                            'fontsize': 20},
    #               alpha=.8,
    #               color=colors
    #               )

    # 使用Squarify导出四边形数据，以数据手动画图，可以控制更多元素
    sizes.sort(reverse=True)  # sizes必须先由大到小排序
    sizes = squarify.normalize_sizes(sizes, width, height)  # 根据设置的总体宽高正态化数据
    rects_data = squarify.squarify(sizes, x, y, width, height)  # Squarify算法计算出所有四边形的数据

    # 根据数据循环创建矩形并添加标签
    for i, r in enumerate(rects_data):
        rect = patches.Rectangle(
            (r["x"], r["y"]), r["dx"], r["dy"], linewidth=2, edgecolor="#222222", facecolor=colors[i]
        )  # 创建四边形
        ax.add_patch(rect)  # Add patch到轴
        # 动态添加标签并设置标签字体大小
        if r["dx"] > 0.02 * (width * height) or r["dx"] * r["dy"] > 0.01 * (width * height):
            plt.text(
                r["x"] + r["dx"] / 2,  # rect的水平中心
                r["y"] + r["dy"] / 2,  # rect的垂直中心
                labels[i],
                ha="center",
                va="center",
                multialignment="center",
                fontproperties=myfont,
                fontsize=80 * r["dx"] / (width * height),
            )
        # 前十名左上角添加Rank
        if i < 10:
            plt.text(
                r["x"] + r["dx"] * 0.1,  # rect的left稍往右偏移
                r["y"] + r["dy"] - r["dx"] * 0.1,  # rect的Top稍往下偏移
                i + 1,
                ha="center",
                va="center",
                multialignment="center",
                fontproperties=myfont,
                fontsize=80 * r["dx"] / (width * height),
            )

    # 去除边框的刻度
    ax.set_xticks([])
    ax.set_yticks([])

    # 添加标题
    if title is not None:
        fig.suptitle(title, fontproperties=myfont)

    # 保存到字符串
    sio = BytesIO()
    plt.savefig(sio, format="png", bbox_inches="tight", transparent=True, dpi=600)
    data = base64.encodebytes(sio.getvalue()).decode()  # 解码为base64编码的png图片数据
    src = "data:image/png;base64," + str(data)  # 增加Data URI scheme

    # 关闭绘图进程
    plt.clf()
    plt.cla()
    plt.close()

    return src


# Matplotlib气泡图
def mpl_bubble(
    x,
    y,
    z,
    labels,
    title,
    x_title,
    y_title,
    x_fmt="{:.0%}",
    y_fmt="{:+.0%}",
    y_avg_line=False,
    y_avg_value=None,
    y_avg_label="",
    x_avg_line=False,
    x_avg_value=None,
    x_avg_label="",
    x_max=None,
    x_min=None,
    y_max=None,
    y_min=None,
    show_label=True,
    label_limit=15,
    z_scale=1,
    color_scheme="随机颜色方案",
    color_list=None,
):

    z = [x * z_scale for x in z]  # 气泡大小系数

    fig, ax = plt.subplots()  # 准备画布和轴
    fig.set_size_inches(15, 10)  # 画布尺寸

    # 手动强制xy轴最小值/最大值
    if x_min is not None and x_min > min(x):
        ax.set_xlim(xmin=x_min)
    if x_max is not None and x_max < max(x):
        ax.set_xlim(xmax=x_max)
    if y_min is not None and y_min > min(y):
        ax.set_ylim(ymin=y_min)
    if y_max is not None and y_max < max(y):
        ax.set_ylim(ymax=y_max)

    # 确定颜色方案
    if color_scheme == "随机颜色方案" or color_scheme is None:
        cmap = mpl.colors.ListedColormap(np.random.rand(256, 3))
        colors = iter(cmap(np.linspace(0, 1, len(x))))
    else:
        if len(x) <= len(color_list):
            colors = color_list[: len(x)]
        else:
            colors = []
            for i in range(len(x)):
                colors.append(color_list[i % len(color_list)])
        colors = iter(colors)

    # 绘制气泡
    for i in range(len(x)):
        ax.scatter(x[i], y[i], z[i], color=next(colors), alpha=0.6, edgecolors="black")

    # 添加系列标签，用adjust_text包保证标签互不重叠
    if show_label is True:
        texts = [
            plt.text(
                x[i],
                y[i],
                labels[i],
                ha="center",
                va="center",
                multialignment="center",
                fontproperties=myfont,
                fontsize=10,
            )
            for i in range(len(labels[:label_limit]))
        ]
        adjust_text(texts, force_text=0.5, arrowprops=dict(arrowstyle="->", color="black"))

    # 添加分隔线（均值，中位数，0等）
    if y_avg_line is True:
        ax.axhline(y_avg_value, linestyle="--", linewidth=1, color="grey")
        plt.text(
            ax.get_xlim()[1],
            y_avg_value,
            y_avg_label,
            ha="left",
            va="center",
            color="r",
            multialignment="center",
            fontproperties=myfont,
            fontsize=10,
        )
    if x_avg_line is True:
        ax.axvline(x_avg_value, linestyle="--", linewidth=1, color="grey")
        plt.text(
            x_avg_value,
            ax.get_ylim()[1],
            x_avg_label,
            ha="left",
            va="top",
            color="r",
            multialignment="center",
            fontproperties=myfont,
            fontsize=10,
        )

    # 设置轴标签格式
    ax.xaxis.set_major_formatter(FuncFormatter(lambda y, _: x_fmt.format(y)))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: y_fmt.format(y)))

    # 添加图表标题和轴标题
    plt.title(title, fontproperties=myfont)
    plt.xlabel(x_title, fontproperties=myfont, fontsize=12)
    plt.ylabel(y_title, fontproperties=myfont, fontsize=12)

    """以下部分绘制回归拟合曲线及CI和PI
    参考
    http://nbviewer.ipython.org/github/demotu/BMC/blob/master/notebooks/CurveFitting.ipynb
    https://stackoverflow.com/questions/27164114/show-confidence-limits-and-prediction-limits-in-scatter-plot
    """
    n = y.size  # 观察例数
    if n > 2:  # 数据点必须大于cov矩阵的scale
        p, cov = np.polyfit(x, y, 1, cov=True)  # 简单线性回归返回parameter和covariance
        poly1d_fn = np.poly1d(p)  # 拟合方程
        y_model = poly1d_fn(x)  # 拟合的y值
        m = p.size  # 参数个数

        dof = n - m  # degrees of freedom
        t = stats.t.ppf(0.975, dof)  # 显著性检验t值

        # 拟合结果绘图
        ax.plot(x, y_model, "-", color="0.1", linewidth=1.5, alpha=0.5, label="Fit")

        # 误差估计
        resid = y - y_model  # 残差
        s_err = np.sqrt(np.sum(resid ** 2) / dof)  # 标准误差

        # 拟合CI和PI
        x2 = np.linspace(np.min(x), np.max(x), 100)
        y2 = poly1d_fn(x2)

        # CI计算和绘图
        ci = t * s_err * np.sqrt(1 / n + (x2 - np.mean(x)) ** 2 / np.sum((x - np.mean(x)) ** 2))
        ax.fill_between(x2, y2 + ci, y2 - ci, color="#b9cfe7", edgecolor="", alpha=0.5)

        # Pi计算和绘图
        pi = t * s_err * np.sqrt(1 + 1 / n + (x2 - np.mean(x)) ** 2 / np.sum((x - np.mean(x)) ** 2))
        ax.fill_between(x2, y2 + pi, y2 - pi, color="None", linestyle="--")
        ax.plot(x2, y2 - pi, "--", color="0.5", label="95% Prediction Limits")
        ax.plot(x2, y2 + pi, "--", color="0.5")

    # 保存到字符串
    sio = BytesIO()
    plt.savefig(sio, format="png", bbox_inches="tight", transparent=True, dpi=600)
    data = base64.encodebytes(sio.getvalue()).decode()  # 解码为base64编码的png图片数据
    src = "data:image/png;base64," + str(data)  # 增加Data URI scheme

    # 关闭绘图进程
    plt.clf()
    plt.cla()
    plt.close()

    return src


def echarts_line(df, datatype="ABS"):
    axislabel_format = "{value}"
    if datatype in ["SHARE", "GR"]:
        df = df.multiply(100).round(2)
        axislabel_format = "{value}%"
    if df.empty is False:
        line = (
            Line()  # init_opts=opts.InitOpts(width="1200px", height="700px")
            .add_xaxis(df.index.strftime("%Y-%m").tolist())
            .set_global_opts(
                # title_opts=opts.TitleOpts(title='Trend', pos_left='center'),
                legend_opts=opts.LegendOpts(pos_top="5%", pos_left="10%", pos_right="60%"),
                toolbox_opts=opts.ToolboxOpts(is_show=True),
                tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross",),
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    boundary_gap=False,
                    splitline_opts=opts.SplitLineOpts(
                        is_show=True, linestyle_opts=opts.LineStyleOpts(type_="dotted", opacity=0.5,),
                    ),
                ),
                yaxis_opts=opts.AxisOpts(
                    type_="value",
                    axislabel_opts=opts.LabelOpts(formatter=axislabel_format),
                    # axistick_opts=opts.AxisTickOpts(is_show=True),
                    splitline_opts=opts.SplitLineOpts(
                        is_show=True, linestyle_opts=opts.LineStyleOpts(type_="dotted", opacity=0.5,),
                    ),
                ),
            )
        )
        for i, item in enumerate(df.columns):
            line.add_yaxis(
                item,
                df[item],
                # symbol='circle',
                symbol_size=8,
                label_opts=opts.LabelOpts(is_show=False),
                linestyle_opts=opts.LineStyleOpts(width=3),
                itemstyle_opts=opts.ItemStyleOpts(border_width=1, border_color="", border_color0="white"),
            )
    else:
        line = Line()

    return line


def echarts_stackbar(
    df,  # 传入数据df，应该是一个行索引为date的时间序列面板数据
    df_gr=None,  # 传入同比增长率df，可以没有
    datatype="ABS",  # 主Y轴形式是绝对值，增长率还是份额，用来确定一些标签格式，默认为绝对值
) -> Bar:

    axislabel_format = "{value}"  # 主Y轴默认格式
    max = df[df > 0].sum(axis=1).max()  # 主Y轴默认最大值
    min = df[df <= 0].sum(axis=1).min()  # 主Y轴默认最小值
    if datatype in ["SHARE", "GR"]:  # 如果主数据不是绝对值形式而是份额或增长率如何处理
        df = df.multiply(100).round(2)
        axislabel_format = "{value}%"
        max = 100
        min = 0
    if df_gr is not None:
        df_gr = df_gr.multiply(100).round(2)  # 如果有同比增长率，原始数*100呈现

    if df.empty is False:
        stackbar = Bar().add_xaxis(df.index.tolist())
        for i, item in enumerate(df.columns):  # 预留的枚举，这个方法以后可以根据输入对象不同从单一柱状图变成堆积柱状图
            stackbar.add_yaxis(
                item, df[item].values.tolist(), stack="总量", label_opts=opts.LabelOpts(is_show=False), z_level=1
            )
            # .add_yaxis(series_name=df.index[-5].strftime("%Y-%m"),
            #            yaxis_data=df_ya.values.tolist(),
            #            stack='总量',
            #            label_opts=opts.LabelOpts(is_show=False)
            #            )
            # .add_yaxis(series_name=df.index[-1].strftime("%Y-%m")+' vs '+df.index[-5].strftime("%Y-%m"),
            #            yaxis_data=df_diff.values.tolist(),
            #            stack='总量',
            #            label_opts=opts.LabelOpts(is_show=False)
            #            )
        if df_gr is not None:  # 如果有同比增长率数据则加入次Y轴
            stackbar.extend_axis(
                yaxis=opts.AxisOpts(name="同比增长率", type_="value", axislabel_opts=opts.LabelOpts(formatter="{value}%"),)
            )
        stackbar.set_global_opts(
            legend_opts=opts.LegendOpts(pos_top="5%", pos_left="10%", pos_right="60%"),
            toolbox_opts=opts.ToolboxOpts(is_show=True),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross",),
            xaxis_opts=opts.AxisOpts(
                type_="category",
                boundary_gap=True,
                axislabel_opts=opts.LabelOpts(rotate=90),  # x轴标签方向rotate有时能解决拥挤显示不全的问题
                splitline_opts=opts.SplitLineOpts(
                    is_show=False, linestyle_opts=opts.LineStyleOpts(type_="dotted", opacity=0.5,),
                ),
            ),
            yaxis_opts=opts.AxisOpts(
                max_=max,
                min_=min,
                type_="value",
                axislabel_opts=opts.LabelOpts(formatter=axislabel_format),
                # axistick_opts=opts.AxisTickOpts(is_show=True),
                splitline_opts=opts.SplitLineOpts(
                    is_show=True, linestyle_opts=opts.LineStyleOpts(type_="dotted", opacity=0.5,),
                ),
            ),
        )
        if df_gr is not None:
            line = (
                Line()
                .add_xaxis(xaxis_data=df_gr.index.tolist())
                .add_yaxis(
                    series_name="同比增长率",
                    yaxis_index=1,
                    y_axis=df_gr.values.tolist(),
                    label_opts=opts.LabelOpts(is_show=False),
                    linestyle_opts=opts.LineStyleOpts(width=3),
                    symbol_size=8,
                    itemstyle_opts=opts.ItemStyleOpts(border_width=1, border_color="", border_color0="white"),
                    z_level=2,
                )
            )
    else:
        stackbar = Bar()

    if df_gr is not None:
        return stackbar.overlap(line)  # 如果有次坐标轴最后要用overlap方法组合
    else:
        return stackbar


def echarts_stackarea(df, datatype="ABS"):
    axislabel_format = "{value}"
    if datatype in ["SHARE", "GR"]:
        df = df.multiply(100).round(2)
        axislabel_format = "{value}%"

    if df.empty is False:
        stackarea = (
            Line()
            .add_xaxis(df.index.strftime("%Y-%m").tolist())
            .set_global_opts(
                # title_opts=opts.TitleOpts(title='Trend', pos_left='center'),
                legend_opts=opts.LegendOpts(pos_top="5%", pos_left="10%", pos_right="60%"),
                toolbox_opts=opts.ToolboxOpts(is_show=True),
                tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross",),
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    boundary_gap=False,
                    splitline_opts=opts.SplitLineOpts(
                        is_show=True, linestyle_opts=opts.LineStyleOpts(type_="dotted", opacity=0.5,),
                    ),
                ),
                yaxis_opts=opts.AxisOpts(
                    type_="value",
                    max_=df.sum(axis=1).max(),
                    axislabel_opts=opts.LabelOpts(formatter=axislabel_format),
                    # axistick_opts=opts.AxisTickOpts(is_show=True),
                    splitline_opts=opts.SplitLineOpts(
                        is_show=True, linestyle_opts=opts.LineStyleOpts(type_="dotted", opacity=0.5,),
                    ),
                ),
            )
        )
        for i, item in enumerate(df.columns):
            stackarea.add_yaxis(
                series_name=item,
                stack="总量",
                y_axis=df[item],
                areastyle_opts=opts.AreaStyleOpts(opacity=0.5),
                # symbol_size=8,
                label_opts=opts.LabelOpts(is_show=False),
                linestyle_opts=opts.LineStyleOpts(width=3),
                itemstyle_opts=opts.ItemStyleOpts(border_width=1, border_color="", border_color0="white"),
            )

    else:
        stackarea = Line()

    return stackarea


def echarts_stackarea100(df, datatype="ABS"):
    axislabel_format = "{value}"
    if datatype in ["SHARE", "GR"]:
        df = df.multiply(100).round(2)
        axislabel_format = "{value}%"

    if df.empty is False:
        stackarea = (
            Line()
            .add_xaxis(df.index.strftime("%Y-%m").tolist())
            .set_global_opts(
                # title_opts=opts.TitleOpts(title='Trend', pos_left='center'),
                legend_opts=opts.LegendOpts(pos_top="5%", pos_left="10%", pos_right="60%"),
                toolbox_opts=opts.ToolboxOpts(is_show=True),
                tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross",),
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    boundary_gap=False,
                    splitline_opts=opts.SplitLineOpts(
                        is_show=True, linestyle_opts=opts.LineStyleOpts(type_="dotted", opacity=0.5,),
                    ),
                ),
                yaxis_opts=opts.AxisOpts(
                    type_="value",
                    max_=100,
                    axislabel_opts=opts.LabelOpts(formatter=axislabel_format),
                    # axistick_opts=opts.AxisTickOpts(is_show=True),
                    splitline_opts=opts.SplitLineOpts(
                        is_show=True, linestyle_opts=opts.LineStyleOpts(type_="dotted", opacity=0.5,),
                    ),
                ),
            )
        )
        for i, item in enumerate(df.columns):
            stackarea.add_yaxis(
                series_name=item,
                stack="总量",
                y_axis=df[item],
                areastyle_opts=opts.AreaStyleOpts(opacity=0.5),
                # symbol_size=8,
                label_opts=opts.LabelOpts(is_show=False),
                linestyle_opts=opts.LineStyleOpts(width=3),
                itemstyle_opts=opts.ItemStyleOpts(border_width=1, border_color="", border_color0="white"),
            )

    else:
        stackarea = Line()

    return stackarea
