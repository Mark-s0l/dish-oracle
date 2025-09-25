'''Был реализован лишь полнотекстовый поиск и incontains,
поскольку триаграммы не справлялись с задачей - получение валидного результата за первые 3-4 символа
при расширении базы данных потребуется пересмотреть использование incontains.'''
from django.contrib.postgres.search import (SearchQuery, SearchRank,
                                            SearchVector)
from django.views.generic import ListView

from search_hub.forms import SearchForm
from food_hub.models import Product


class ProductSearchView(ListView):
    model = Product
    template_name = "search_hub/search_page.html"
    context_object_name = "products"

    def get_queryset(self):
        self.form = SearchForm(self.request.GET)
        if self.form.is_valid(): 
            query = self.form.cleaned_data["query"]
            if not query.strip(): return Product.objects.none()
            search_vector = (SearchVector("name", weight="A", config="russian") +
                            SearchVector("company__name", weight="B", config="russian") +
                            SearchVector("category__name", weight="C", config="russian")) 
            search_query = SearchQuery(query, config="russian", search_type="websearch")
            results = ( Product.objects.annotate( 
                                                search=search_vector, 
                                                rank=SearchRank(search_vector, 
                                                                search_query), )
                       ).filter(search=search_query).order_by("-rank") 
            if not results.exists():
                return Product.objects.filter(name__icontains=query).select_related("company", "category")
            return results 
        else:                 
            return Product.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        context["query"] = self.request.GET.get("query", "")
        return context