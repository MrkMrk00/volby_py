from collections import namedtuple
import matplotlib.pyplot as plt

import requests
from xml.etree import ElementTree as ET

NUTS_KRAJE = [
    'CZ010', 'CZ020', 'CZ031',
    'CZ032', 'CZ041', 'CZ042',
    'CZ052', 'CZ053', 'CZ063',
    'CZ064', 'CZ071', 'CZ072',
    'CZ080'
]

KANDIDATI = {
    1: 'Fischer',
    2: 'Bašta',
    4: 'Pavel',
    5: 'Zima',
    6: 'Nerudová',
    7: 'Babiš',
    8: 'Diviš',
    9: 'Hilšer'
}

VYSLEDKY_URL = 'https://www.volby.cz/pls/prez2023/vysledky_kraj'
NAMESPACES = { '': 'http://www.volby.cz/prezident/' }


class Vysledky(object):
    def __init__(self, nuts, nazev, vysledky):
        self.nuts = nuts
        self.nazev = nazev
        self.vysledky = vysledky

    @staticmethod
    def handle_vysledky(vysledky_element):
        vysl_map = {}
        kandidati = vysledky_element.findall('CELKEM/HODN_KAND', namespaces=NAMESPACES)
        for kandidat in kandidati:
            vysl_map[int(kandidat.attrib['PORADOVE_CISLO'])] = int(kandidat.attrib['HLASY'])
        return vysl_map

    def pocet_hlasu(self):
        return sum(self.vysledky.values())

    def vysledky_procenta(self):
        celkem = self.pocet_hlasu()
        res = {}
        for kand, hlasy in self.vysledky.items():
            res[kand] = hlasy / celkem * 100

        return res


class KrajVysledky(Vysledky):
    @classmethod
    def from_xml(cls, xml_text):
        etree = ET.fromstring(xml_text)
        kraj = etree.find('KRAJ', namespaces=NAMESPACES)

        return cls(
                kraj.attrib['NUTS_KRAJ'],
                kraj.attrib['NAZ_KRAJ'],
                cls.handle_vysledky(kraj)
        )


class OkresVysledky(Vysledky):
    @classmethod
    def from_xml(cls, xml_text):
        etree = ET.fromstring(xml_text)

        okres_vysl = etree.findall('KRAJ/OKRES', namespaces=NAMESPACES)
        okresy = []

        for okr in okres_vysl:
            okresy.append(cls(
                okr.attrib['NUTS_OKRES'],
                okr.attrib['NAZ_OKRES'],
                cls.handle_vysledky(okr)
            ))

        return okresy


def get_kraj(nuts):
    params = {
        'kolo': 1,
        'nuts': nuts
    }

    retry = 0
    res = None

    while res is None:
        try:
            print(f'Getting for NUTS {nuts}; retry={retry}')
            res = requests.get(url=VYSLEDKY_URL, params=params, allow_redirects=True, timeout=0.5)

        except Exception:
            if retry >= 5:
                raise Exception('Max retries')
            retry += 1

    return res.text


def for_display(vysledky, pct=False):
    vysl = vysledky.vysledky
    if pct:
        vysl = vysledky.vysledky_procenta()

    res = {}
    for cislo, jmeno in KANDIDATI.items():
        res[jmeno] = vysl[cislo]

    return res


def pie(sub_plot, obj):
    vysl = for_display(obj)
    sizes = list(vysl.values())
    labels = list(vysl.keys())
    sub_plot.pie(
        sizes, labels=labels, autopct='%1.1f%%',
        shadow=True, startangle=90, pctdistance=0.9,
        labeldistance=1.2, radius=2)
    sub_plot.set_title(obj.nazev)
    sub_plot.axis('equal')


def bar(sub_plot, obj):
    vysl = for_display(obj)

    x = list(vysl.keys())
    y = list(vysl.values())

    sub_plot.set_title(obj.nazev)
    sub_plot.bar(x, height=y)
    sub_plot.set_xticklabels(x, rotation=45, ha='right')


def main():
    plt.figure()
    sp, axies = plt.subplots(2, 7, figsize=(19.2, 10.8), dpi=100)
    for i, krajNuts in enumerate(NUTS_KRAJE):
        res = get_kraj(krajNuts)
        kraj = KrajVysledky.from_xml(res)
        bar(axies[i % 2, int(i/2)], kraj)

    sp.delaxes(axies[1, 6])
    plt.tight_layout()
    plt.show()




if __name__ == '__main__':
    main()
