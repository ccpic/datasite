/**
 * jQuery plugin offering simple tag selector.
 * for usage, please refer to the `demo.html'.
 *
 * The MIT License (MIT)
 *
 * Copyright (c) 2015 peixu.zhu (朱培旭)
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */
(function($){
    if (undefined === $.fn.tag_selector ){
        $.fn.tag_selector = function(options){
            var that = this;
            var settings = $.extend({
                class_prefix : null
                , multi_select: false
                , data  : []
                , callback: null
            }, options);
            //
            if( null == settings.class_prefix){
                throw 'class_prefix must be set to create a tag selector.';
            }
            var html = '';
            var data_item;
            var class_name = settings.class_prefix + '_' + 'tag';
            var tag_class_selected = class_name + '_selected';
            var tag_class_unselected = class_name + '_unselected';
            var tag_class_name;
            var data_selected = [];
            var data_unselected = [];

            for( var i in settings.data){
                data_item = settings.data[i];
                tag_class_name = class_name;
                if (data_item.selected){
                    tag_class_name += ' ' + tag_class_selected;
                }
                else{
                    tag_class_name += ' ' + tag_class_unselected;
                }
                html += '<div data-value="' + data_item.value + '" class="' + tag_class_name +'"' + '>' + data_item.label + '</div>\n';
            }
            $(this).html(html);
            //
            function stat_selected(){
                var collect = $('.' + tag_class_selected);
                var i, d;
                data_selected = Array();
                data_unselected = Array();
                for(i = 0; i < collect.length; i++){
                    d = $(collect[i]);
                    data_selected.push({value: d.data('value'), label: d.text()});
                }
                collect = $('.' + tag_class_unselected);
                for(i = 0; i < collect.length; i++){
                    d = $(collect[i]);
                    data_unselected.push({value: d.data('value'), label: d.text()});
                }
                $(that).data('selected', JSON.stringify(data_selected));
                $(that).data('unselected', JSON.stringify(data_unselected));
            }
            stat_selected();
            //
            $('.' + class_name).on('click',function(){
                var me = $(this);
                var event_name;
                if (me.hasClass(tag_class_selected)){
                    me.removeClass(tag_class_selected);
                    me.addClass(tag_class_unselected);
                    event_name = 'unselected';
                }
                else{
                    if (! settings.multi_select){
                        var all_tags = $('.' + class_name);
                        all_tags.removeClass(tag_class_selected);
                        all_tags.addClass(tag_class_unselected);
                    }
                    me.removeClass(tag_class_unselected);
                    me.addClass(tag_class_selected);
                    event_name = 'selected';
                }
                stat_selected();
                if (settings.callback){
                    settings.callback(event_name, this, that);
                }
            });
        }
    }
})(jQuery);
