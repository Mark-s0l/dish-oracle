from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.postgres.search import (SearchQuery, SearchRank,
                                            SearchVector)
from django.db.models import Q
from django.views.generic import ListView

from food_hub.models import Product
from search_hub.forms import SearchForm, TagSelectorForm


class ProductSearchView(ListView):
    model = Product
    template_name = "search_hub/search_page.html"
    context_object_name = "products"

    def get_queryset(self):
        # Формирование базового queryset
        # ArrayAgg собирает значения из нескольких строк в один массив
        # distunct=True - убираем дубликаты
        qs = (
            Product.objects.select_related("company", "category")
            .prefetch_related("ratings__taste_tags")
            .annotate(tag_names=ArrayAgg("ratings__taste_tags__name", distinct=True))
        )
        get_data = self.request.GET.copy()
        if get_data.get("action") == "clear":
            get_data.pop("tags", None)

        tag_form = TagSelectorForm(get_data)
        self._tag_form_for_context = tag_form

        tag_ids = []
        if tag_form.is_valid():
            # flat - ['values'] вместо [('values',)]
            tag_ids = list(tag_form.cleaned_data["tags"].values_list("id", flat=True))
            if tag_ids:
                qs = qs.annotate(
                    tag_ids=ArrayAgg("ratings__taste_tags__id", distinct=True)
                    )
                qs = qs.filter(tag_ids__contains=tag_ids)

        # Поисковая форма
        self.searchform = SearchForm(self.request.GET)
        if not self.searchform.is_valid():
            return qs.none()

        query = (self.searchform.cleaned_data.get("query") or "").strip()
        if not query:
            if tag_ids:
                return qs.distinct()
            return qs.none()
        # Префикс поиск
        prefix_qs = qs.filter(
            Q(name__istartswith=query)
            | Q(company__name__istartswith=query)
            | Q(category__name__istartswith=query)
        ).order_by("name")
        if prefix_qs.exists():
            return prefix_qs
        # FTS поиск
        vector = (  # Приоритет поиска - name, company name, category name
            SearchVector("name", weight="A", config="russian")
            + SearchVector("company__name", weight="B", config="russian")
            + SearchVector("category__name", weight="C", config="russian")
        )
        search_query = SearchQuery(query, config="russian", search_type="websearch")
        # SearchRank вычисляет релевантность (вес совпадения) для сортировки результатов
        fts_qs = (
            qs.annotate(search=vector, rank=SearchRank(vector, search_query))
            .filter(search=search_query)
            .order_by("-rank", "name")
        )

        if fts_qs.exists():
            return fts_qs

        # icontains поиск
        return qs.filter(
            Q(name__icontains=query)
            | Q(company__name__icontains=query)
            | Q(category__name__icontains=query)
        ).order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.searchform
        context["tag_selector"] = getattr(
            self, "_tag_form_for_context", TagSelectorForm(self.request.GET)
            )
        context["query"] = self.request.GET.get("query", "")
        return context
