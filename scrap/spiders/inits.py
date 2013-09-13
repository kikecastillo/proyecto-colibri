# coding=utf-8
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import HtmlXPathSelector

from dateutil import parser as dparser
import re

from initiatives.models import Initiative
from member.models import Member
from term.models import Term

ACTUAL_TERM = Term.objects.latest('id')


class MemberSpider(CrawlSpider):
    name = 'initiatives'
    allowed_domains = ['congreso.es', ]
    start_urls = ['http://www.congreso.es/portal/page/portal/Congreso/Congreso/Iniciativas/Indice de Iniciativas', ]
    rules = [
        Rule(SgmlLinkExtractor(
            allow=['/portal/page/portal/Congreso/Congreso/Iniciativas/Indice%20de%20Iniciativas\?_piref73_1335503_73_1335500_1335500\.next_page=/wc/servidorCGI&CMD=VERLST&BASE=IW10&PIECE=IWC0&FMT=INITXD1S\.fmt&FORM1=INITXLUS\.fmt&DOCS=\d+-\d+&QUERY=%28I%29\.ACIN1\.\+%26\+%28\d{3}%29\.SINI\.']), 'parse_initiative'),
        Rule(SgmlLinkExtractor(
            allow=['/portal/page/portal/Congreso/Congreso/Iniciativas/Indice%20de%20Iniciativas\?_piref73_1335503_73_1335500_1335500\.next_page=/wc/servidorCGI&CMD=VERLST&BASE=IW10&PIECE=IWA0&FMT=INITXD1S\.fmt&FORM1=INITXLUS\.fmt&DOCS=\d+-\d+&QUERY=%28I%29\.ACIN1\.\+%26\+%28\d{3}%29\.SINI\.']), 'parse_initiative'),
        Rule(SgmlLinkExtractor(
            allow=['/portal/page/portal/Congreso/Congreso/Iniciativas/Indice%20de%20Iniciativas\?_piref73_1335503_73_1335500_1335500\.next_page=/wc/servidorCGI&CMD=VERLST&BASE=IW10&FMT=INITXLUS\.fmt&DOCS=\d+-\d+&DOCORDER=FIFO&OPDEF=Y&QUERY=%28I%29\.ACIN1\.\+%26\+%28181%29\.SINI\.']), follow=True),]

    def parse_initiative(self, response):
        x = HtmlXPathSelector(response)
        initiative = None
        title_xpath = x.select('//p[@class="titulo_iniciativa"]/text()')
        if title_xpath:
            record = title_xpath.re('(\d+/\d+)').pop()
            initiative, created = Initiative.objects.get_or_create(record=record, term=ACTUAL_TERM)
            title = title_xpath.pop().extract()

            initiative_type = x.select('//p[@class="subtitulo_competencias"]/text()').pop().extract()
            dates = x.select('//div[@class="resultados"]/div[@class="ficha_iniciativa"]/p[@class="texto"]/text()')

            register_date_re = dates.re('Presentado el \d{2}/\d{2}/\d{4}')
            register_date = dparser.parse(register_date_re.pop(), fuzzy=True).date() if register_date_re else None
            calification_date_re = dates.re('calificado el \d{2}/\d{2}/\{4}')
            calification_date = dparser.parse(calification_date_re.pop(), fuzzy=True).date() if register_date_re else None

            author_dip_re = x.select('//div[@id="RESULTADOS_BUSQUEDA"]/div[@class="resultados"]/div[@class="ficha_iniciativa"]/p[@class="texto"]/a').re('idDiputado=\d+')
            author_dip_id = re.sub('idDiputado=', '', author_dip_re.pop()) if author_dip_re else None

            initiative.record = record
            initiative.title = title
            initiative.register_date = register_date
            initiative.calification_date = calification_date
            initiative.initiative_type = initiative_type
            initiative.author = Member.objects.get(congress_id__exact=author_dip_id)
            initiative.save()

        return initiative
