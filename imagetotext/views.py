import os
import re

from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ImageUploadForm
from django.http import FileResponse, HttpResponse
from .forms import ContactForm
from .models import Contact, CustomPage, Blog
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from decouple import config
import replicate
from docx import Document
from io import BytesIO


def index(request):
    # Set the REPLICATE_API_TOKEN environment variable
    os.environ["REPLICATE_API_TOKEN"] = config('REPLICATE_API_TOKEN')
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            myForm = form.save(commit=False)
            myForm.save()
            # Use request.build_absolute_uri() to build the full URL
            full_url = request.build_absolute_uri(settings.MEDIA_URL + myForm.image.name)
            try:
                output = replicate.run(
                    "abiruyt/text-extract-ocr:a524caeaa23495bc9edc805ab08ab5fe943afd3febed884a4f3747aa32e9cd61",
                    input={
                        "image": full_url
                    }
                )
            except Exception as e:
                output = f'e {e}'
            return render(request, 'index.html', {'output_text': output, 'full_url': full_url})
    else:
        form = ImageUploadForm()
    return render(request, 'index.html', {'form': form})


def clean_html(raw_html):
    cleanR = re.compile('<.*?>')  # HTML etiketlerini tanımlayan düzenli ifade
    cleantext = re.sub(cleanR, '', raw_html)  # Etiketleri boş string ile değiştir
    return cleantext

def download_txt(request):
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="download.txt"'
    text = request.GET.get('text')
    newText = clean_html(text)
    response.write(newText)
    return response


def download_docx(request):
    document = Document()
    text = request.GET.get('text')
    newText = clean_html(text)
    document.add_paragraph(newText)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = 'attachment; filename="download.docx"'
    buffer = BytesIO()
    document.save(buffer)
    response.write(buffer.getvalue())
    return response


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you! We will reach out to you as soon as possible.")
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})


def custom_page(request, slug=None):
    content = get_object_or_404(CustomPage, slug=slug)
    return render(request, 'custom.html', {'content': content})


def blog(request):
    blog_list = Blog.objects.all().order_by('-publish')  # Assuming there's a date_posted field
    paginator = Paginator(blog_list, 10)  # Show 10 blogs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'blog.html', {'page_obj': page_obj})


def blog_detail(request, slug=None):
    blogDetail = get_object_or_404(Blog, slug=slug)
    return render(request, 'blog_detail.html', {'post': blogDetail})


def robots_txt(request):
    lines = [
        "User-Agent: *",
        "Disallow: /admin/",
        "Allow: /",
        "Sitemap: https://www.image2textai.com/sitemap.xml"
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
