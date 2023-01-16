# Detekcia prispievateľov do online diskusie typu troll

Samuel Gecík

Sémantický a sociálny web,
2022

---

Detekcia trollov v diskusiách je proces identifikácie a filtrovania urážlivých alebo rušivých komentárov na online platformách. Môže zahŕňať použitie algoritmov a techník strojového učenia na nahlásenie komentárov, ktoré obsahujú nepravdivé informácie, nenávistné prejavy alebo osobné útoky. Okrem automatizovaných softvérových riešení sa využívajú aj ľudskí moderátori, ktorí môžu tiež kontrolovať komentáre, aby zabezpečili bezpečné prostredie pre používateľov. Pre online platformy je dôležité, aby mali zavedený robustný systém na detekciu trollov, a tým udržiavali zdravú komunitu a vytvorili bezpečný priestor pre všetkých ľudí, ktorí na nich vytvárajú alebo konzumujú obsah.

## Cieľ

Cieľom tohto zadania bolo vytvorenie aplikácie zabezpečujúcej detekciu používateľov typu troll v komentároch na platforme YouTube.

## Riešenie

Dosiahnuť svoj cieľ sa zadanie snaží prostredníctvom filtrovania najaktívnejších prispievateľov. Užívateľ aplikácie si nastaví YouTube kanály, na ktoré sa chce zamerať, takisto ako aj počet videí, z ktorých budú dáta extrahované. Ďalej taktiež nastaví počet strán komentárov pod videom, ktoré budú stiahnuté. Následne aplikácia pomocou oficiálneho API stiahne všetky žiadané údaje a vytvorí dve jednoduché databázy vo forme CSV súborov.

## Štruktúra

Hlavná štruktúra aplikácie pozostáva z modulov ``analysis.py``, ``collect_data.py`` a ``datasets.py``. V prvom menovanom module sa nachádzajú funkcie zodpovedné za analýzu dát, v druhom funkcie na získavanie dát a v treťom je definícia triedy zabezpečujúcej manipuláciu s dátami, ako aj ukladanie dát do databáz.

Počas behu programu sú takisto podľa zvolených funkcií generované rôzne súbory, ako napríklad už spomenuté databázy alebo aj natrénované modely na vektorizáciu pojmov.

Pre testovacie účely slúži Jupyter notebook ``test.ipynb``, kde si používateľ môže skúšať rôzne implementované funkcie.

## Detekcia

Hlavným prvkom tohto zadania je funkcia ``experiment_troll_detection()``, ktorá má za úlohu na grafoch vykresliť aktivitu podozrivých používateľov v čase, pre používateľom zvolené kanály.

Ďalej je používateľovi k dispozícii tiež funkcia ``get_comments_dataframes()``, navracajúca dátové rámce pre každý zvolený kanál, v ktorých sú zoradený prispievatelia podľa počtu pridaných komentárov.

Získané informácie môžu byť dodatočne podrobené manuálnej kontrole alebo hlbšej analýze.

## Doplnkové funkcie

V module ``analysis.py`` sú definované aj doplnkové funkcie, slúžiace na hlbšiu analýzu dát. Tieto funkcie zahŕňajú metódy ako detekcia rovnakých príspevkov, vektorizácia slov a následné zhlukovanie pojmov podľa podobnosti, ako aj dimenzionálu redukciu a vykreslenie zhlukov na graf. Využívanie týchto funkcií sa však odporúča iba v experimentálnej rovine, vzhľadom na možnú nestabilitu ich fungovania.
