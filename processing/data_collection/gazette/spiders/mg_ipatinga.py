from dateparser import parse

import datetime as dt
import ast

from gazette.items import Gazette

from .mg_governador_valadares import GVSpiderAbastract

class MGIpatinga(GVSpiderAbastract):
    MUNICIPALITY_ID = '3131307'
    name = 'mg_ipatinga'
    allowed_domains = ['ipatinga.mg.gov.br']
    start_urls = ['http://www.ipatinga.mg.gov.br/ajaxpro/diel_diel_lis,App_Web_diel_diel_lis.aspx.cdcab7d2.nvlaomdm.ashx']
    
    def parse(self, response):
        
        rows = self.parse_body(response)
        if not rows:
            return

        for row in rows:
            params = self.parse_row(self.MUNICIPALITY_ID, row)
            self.logger.info(params)
            #yield Gazette(**params)

        yield self.next_request()