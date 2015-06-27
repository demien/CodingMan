from django.views.generic import View
from django.shortcuts import render_to_response
from django.utils.safestring import mark_safe
import json
from .services import get_similar_tags, get_apps_by_tag


class HomeView(View):
    TOP_N_TAGS = ['iphone', 'app']
    TOP_N_TAGS_CLASS = ['news', 'money', 'tech', 'sports', 'auto', 'ent']

    def get(self, request, *args, **kwargs):
        tag_objs = []
        for tag in self.TOP_N_TAGS:
            similar_tags = get_similar_tags(tag)
            similar_tag_objs = []
            for similar_tag in similar_tags:
                app_objs = get_apps_by_tag(similar_tag)
                tagObj = {
                    'tagName': similar_tag[0],
                    'tagMessage': ' ; '.join([app['title'] for app in app_objs[:2]]),
                    'imgs': app_objs
                }
                similar_tag_objs.append(tagObj)
            tag_objs.append(similar_tag_objs)
        tag_css = ['news', 'money', 'tech', 'sports', 'auto', 'ent']
        top_tags = zip(self.TOP_N_TAGS, self.TOP_N_TAGS_CLASS)
        return render_to_response('home.html', {'tagDatas': mark_safe(json.dumps(tag_objs)), 'top_tags': top_tags})