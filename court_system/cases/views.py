from django.views.generic import ListView, CreateView, DetailView
from django.urls import reverse_lazy
from .models import Case
from .utils import generate_case_number

class CaseListView(ListView):
    model = Case
    template_name = 'cases/case_list.html'
    context_object_name = 'cases'
    ordering = ['-filing_date', '-id']

class CaseCreateView(CreateView):
    model = Case
    template_name = 'cases/case_form.html'
    fields = ['title', 'case_type', 'description']
    success_url = reverse_lazy('case_list')

    def form_valid(self, form):
        # Generate case number before saving
        form.instance.case_number = generate_case_number(form.instance.case_type)
        return super().form_valid(form)

class CaseDetailView(DetailView):
    model = Case
    template_name = 'cases/case_detail.html'
    context_object_name = 'case'
    slug_field = 'case_number'
    slug_url_kwarg = 'case_number'
