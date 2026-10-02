"""Recursos de SEO servidos pelo backend."""
from django.conf import settings
from django.http import HttpResponse
from django.utils.xmlutils import SimplerXMLGenerator
from io import StringIO


def robots_txt(request):
    linhas = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin",
        "Disallow: /api/",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(linhas), content_type="text/plain")


def sitemap_noticias(request):
    """Sitemap com as noticias publicadas, apontando para o frontend."""
    from apps.news.models import Noticia

    saida = StringIO()
    xml = SimplerXMLGenerator(saida, "utf-8")
    xml.startDocument()
    xml.startElement("urlset", {"xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9"})

    def adicionar(caminho, alteracao, prioridade, data=None):
        xml.startElement("url", {})
        xml.addQuickElement("loc", f"{settings.SITE_URL}{caminho}")
        if data:
            xml.addQuickElement("lastmod", data.date().isoformat())
        xml.addQuickElement("changefreq", alteracao)
        xml.addQuickElement("priority", prioridade)
        xml.endElement("url")

    adicionar("/", "hourly", "1.0")
    adicionar("/tendencias", "hourly", "0.7")
    adicionar("/videos", "daily", "0.6")

    noticias = (
        Noticia.objects.publicadas()
        .order_by("-data_publicacao")
        .values_list("slug", "data_atualizacao")[:5000]
    )
    for slug, atualizado in noticias:
        adicionar(f"/noticia/{slug}", "daily", "0.8", atualizado)

    xml.endElement("urlset")
    xml.endDocument()
    return HttpResponse(saida.getvalue(), content_type="application/xml")
