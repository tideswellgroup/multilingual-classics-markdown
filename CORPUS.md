# Corpus inventory

Curated public-domain literary classics across 58 locales (47 beyond modern English, plus the historical and regional Englishes), with YAML frontmatter declaring source, year, license, and provenance. This corpus is intended as the non-English complement to [`mlschmitt/classic-books-markdown`](https://github.com/mlschmitt/classic-books-markdown).

## Provenance

The books came from eleven upstream sources, each with its own conventions:

| Source | Locales sourced from it |
|---|---|
| [Project Gutenberg](https://www.gutenberg.org) | de-DE, de-AT, es-ES, fr-FR, fr-CA (Conan), fi, is (sagadb relay), it, nl, sv, cs (Čapek), pt-PT, pt-BR, ru second, ang, sco, en-IE, en-CA, en-NZ, en-ZA, en-AU, en-IN, haw (both books, Distributed Proofreaders transcriptions; re-sourced 2026-07-24) |
| Wikisource (per-language) | el (Papadiamantis stories), hi, ar, fa (Saadi), it, vi, th, cy, fi second, ru third, uk, zh-Hans, zh-Hant, ko, ur, he second, pl, bn, ta (Bharati), enm (Skeat text), en-GB (1609 Quarto), en-US (1855 Leaves), en-JM, la (Greenough text) |
| [Aozora Bunko](https://www.aozora.gr.jp) | ja Akutagawa, ja Mori Ōgai, ja Sōseki, ja Terada (two science essays) |
| [Project Ben-Yehuda](https://benyehuda.org) | he Brenner, he Bialik |
| [Ganjoor.net](https://ganjoor.net) | fa Khayyam *Rubaiyat*, fa Hafez Ghazaliyat |
| [Saga Database](https://sagadb.org) | is *Hrafnkels saga*, is *Brennu-Njáls saga*, is *Eyrbyggja saga* |
| [Internet Archive](https://archive.org) | yo Crowther, yo Dennett, yo Bowen, sw Velten, es-MX Frías, gd Mac an t-Saoir, chr Cherokee Constitution, mi *Nga Mahinga* (1854 first edition) |
| Wikisource (multilingual) | ga Ó Conaire, sw Steere, sw Makunganya, io Jespersen, vo gazette anthology |
| [Project Madurai](https://www.projectmadurai.org) | ta *Tirukkural*, ta *Kuṟuntokai* |
| NZETC (Victoria University of Wellington), via Internet Archive Wayback Machine | mi Grey *Ko Nga Moteatea*, mi White *Nga Kauhau Maori o Nehe* (live host decommissioned; retrieval CDX-verified) |
| [africanpoems.net](https://africanpoems.net) | sw Mwana Kupona |

Each `.md` file's frontmatter records the precise source URL, the upstream repository, the original publication year, and a US public-domain license declaration.

## Curation principles

1. **Every book is unambiguously in the US public domain**: normally that means pre-1929 publication; a narrow documented manuscript-works exception (author dead before 1855, unpublished-works term long expired, basis stated in the file's source_note) also qualifies.
2. **The selection is secular**, excluding the sacred and liturgical texts of every religion alike. Folk-tale corpora, national epics, philosophical-skeptical works, and reference works are included as literary canon. Works specifically judged literary: Khayyam *Rubaiyat* (philosophical-skeptical), *Alf laylah wa-laylah* (framed-narrative folk fiction), *Lazarillo de Tormes* (anti-clerical satire), Saadi *Gulistan* (ethical prosimetric in the wisdom-literature tradition), the Mabinogi (medieval Welsh folk tales with mythological content), *Dao De Jing* and *Analects* (philosophical canon), Bowen *Yoruba Proverbs* and Cherokee *Constitution* (secular alternatives to the overwhelmingly missionary-religious pre-1929 corpora in those languages).
3. **Each locale carries two to three books** where sources permitted, mixing size, genre, and period, and differentiating by register or epoch within the locale.
4. **Canonical works are preferred** over obscure ones.
5. **Reference works are accepted as locale-fillers** only where literary prose is not digitised in clean form. This currently applies to yo (Crowther dictionary, Dennett primer, Bowen proverbs) and chr (the Cherokee Nation Constitution is the only substantive pre-1929 secular Cherokee-language source on Internet Archive).

## Editorial method and limitations

Everything in this file records judgment calls rather than settled facts. Sources are volunteer digitisations taken on trust plus the fidelity audits described in the conversion caveats; attributions follow the cited editions except where scholarship identifies uncredited source authors (collected oral literature especially), in which case the frontmatter credits them; year fields follow the source edition with nuance in year_note. Corrections, better sources, and challenges to any pick are welcome via the content-correction issue template.

## Inventory

137 markdown files across 58 locales. Sizes are approximate.

### Cluster A: Indo-European Romance

| Locale | Author | Title | Year | Size |
|---|---|---|---|---|
| es-ES | Anonymous | *Lazarillo de Tormes* | 1554 | 109 KB |
| es-ES | Miguel de Cervantes Saavedra | *Don Quijote* Part I | 1605 | 1.02 MB |
| es-ES | Gustavo Adolfo Bécquer | *Obras escogidas* (Leyendas + Rimas) | 1871 | 545 KB |
| es-MX | Mariano Azuela | *Los de abajo* | 1915 | 211 KB |
| es-MX | Amado Nervo | *Perlas negras* | 1898 | 33 KB |
| es-MX | Heriberto Frías | *Tomóchic* | 1893 | 383 KB |
| es-MX | Ignacio Manuel Altamirano | *El Zarco* | 1901 | 290 KB |
| fr-FR | Guy de Maupassant | *Boule de Suif* | 1880 | 119 KB |
| fr-FR | Victor Hugo | *Notre-Dame de Paris* | 1831 | 1.08 MB |
| fr-FR | Voltaire | *Candide* | 1759 | 201 KB |
| fr-CA | Philippe Aubert de Gaspé | *Les Anciens Canadiens* | 1863 | 721 KB |
| fr-CA | Laure Conan | *Angéline de Montbrun* | 1884 | 266 KB |
| it | Giovanni Boccaccio | *Decameron* Proemio + Giornata I (1-3) | 1353 | 89 KB |
| it | Carlo Collodi | *Le avventure di Pinocchio* | 1883 | 247 KB |
| it | Giacomo Leopardi | *I Canti* (Hoepli 1920 ed.) | 1835 | 153 KB |
| pt-PT | Eça de Queirós | *O Mandarim* | 1880 | 125 KB |
| pt-PT | Camilo Castelo Branco | *Amor de Perdição* | 1862 | 290 KB |
| pt-PT | Almeida Garrett | *Viagens na Minha Terra* | 1846 | 435 KB |
| pt-BR | Machado de Assis | *Memorias Posthumas de Braz Cubas* | 1881 | 372 KB |
| pt-BR | José de Alencar | *Iracema* | 1865 | 184 KB |
| pt-BR | Bernardo Guimarães | *A Escrava Isaura* | 1875 | 314 KB |

### Cluster B: Indo-European Germanic / Nordic

| Locale | Author | Title | Year | Size |
|---|---|---|---|---|
| de-DE | Franz Kafka | *Die Verwandlung* | 1915 | 124 KB |
| de-DE | E. T. A. Hoffmann | *Der Sandmann* | 1816 | 81 KB |
| de-DE | Johann Wolfgang von Goethe | *Die Leiden des jungen Werthers* | 1774 | 239 KB |
| de-AT | Arthur Schnitzler | *Leutnant Gustl* | 1900 | 79 KB |
| de-AT | Hugo von Hofmannsthal | *Der Tor und der Tod* | 1893 | 27 KB |
| de-AT | Stefan Zweig | *Brennendes Geheimnis* | 1911 | 140 KB |
| nl | Multatuli | *Max Havelaar* | 1860 | 734 KB |
| nl | Frederik van Eeden | *De kleine Johannes* | 1885 | 217 KB |
| sv | August Strindberg | *Röda rummet* | 1879 | 587 KB |
| sv | Selma Lagerlöf | *Bannlyst* | 1918 | 432 KB |
| no | Knut Hamsun | *Markens grøde* | 1917 | 639 KB |
| is | Anonymous | *Hrafnkels saga Freysgoða* | c. 1300 | 56 KB |
| is | Anonymous | *Brennu-Njáls saga* | c. 1280 | 611 KB |
| is | Anonymous | *Eyrbyggja saga* | c. 1250 | 219 KB |
| fi | Eino Leino | *Helkavirsiä* | 1903 | 77 KB |
| fi | Aleksis Kivi | *Seitsemän veljestä* | 1870 | 657 KB |
| fi | Juhani Aho | *Juha* | 1911 | 238 KB |

### Cluster C: Indo-European Slavic + Celtic

| Locale | Author | Title | Year | Size |
|---|---|---|---|---|
| ru | Aleksandr Sergeevich Pushkin | *Пиковая дама* | 1834 | 76 KB |
| ru | Lev Nikolaevich Tolstoy | *Смерть Ивана Ильича* | 1886 | 197 KB |
| ru | Nikolai Vasilyevich Gogol | *Шинель* | 1842 | 115 KB |
| uk | Taras Shevchenko | *Кобзарь* (1840 first edition) | 1840 | 39 KB |
| uk | Lesia Ukrainka | *Лісова пісня* | 1912 | 91 KB |
| uk | Mykhailo Kotsiubynsky | *Тіні забутих предків* | 1912 | 98 KB |
| cy | Anhysbys | *Pwyll, Pendefig Dyfed* | Edwards 1907 | 36 KB |
| cy | Anhysbys | *Branwen ferch Llŷr* | Edwards 1907 | 27 KB |
| cy | Anhysbys | *Manawydan uab Llyr* (Middle Welsh) | 14th c. ms. | 24 KB |
| ga | Pádraic Ó Conaire | *An crann géagach* | 1919 | 104 KB |
| gd | Donnchadh Bàn Mac an t-Saoir | *Moladh Beinn-Dòrain* | 1768 (1912 Calder ed.) | 16 KB |
| cs | Božena Němcová | *Babička* | 1855 | 468 KB |
| cs | Karel Čapek | *R.U.R.* | 1920 | 121 KB |
| pl | Adam Mickiewicz | *Pan Tadeusz* (Księgi I-II) | 1834 | 88 KB |
| pl | Bolesław Prus | *Kamizelka* | 1882 | 20 KB |
| pl | Jan Kochanowski | *Treny* | 1580 | 27 KB |

### Cluster D: Indo-European Indic + Afro-Asiatic

| Locale | Author | Title | Year | Size |
|---|---|---|---|---|
| hi | Premchand | *पंच परमेश्वर* | 1916 | 55 KB |
| hi | Bhartendu Harishchandra | *अंधेर नगरी* | 1881 | 47 KB |
| hi | Premchand | *नमक का दारोगा* | 1916 | 47 KB |
| ur | Muhammad Iqbal | *بانگ درا / Bang-e-Dara* | 1924 | 338 KB |
| ur | Mirza Ghalib | *دیوان غالب / Divan-e-Ghalib* | 1869 | 224 KB |
| ur | Mir Taqi Mir | *ساقی نامہ و جنگ نامہ* | c. 1810 | 16 KB |
| bn | Rabindranath Tagore | *গীতাঞ্জলি* | 1913 | 164 KB |
| bn | Sarat Chandra Chattopadhyay | *দেবদাস* | 1917 | 392 KB |
| bn | Bankim Chandra Chattopadhyay | *কপালকুণ্ডলা* | 1870 | 395 KB |
| he | Yosef Haim Brenner | *מסביב לנקודה* | 1904 | 367 KB |
| he | Hayim Nahman Bialik | *אריה בעל גוף* | 1898 | 132 KB |
| he | Sholem Aleichem | *שושנה* | 1888 | 32 KB |
| ar | Anonymous | *ألف ليلة وليلة* Part I | Bulaq 1835 | 235 KB |
| ar | Ibn Tufayl | *حي بن يقظان* | c. 1175 | 176 KB |
| ar | al-Hariri | *مقامات الحريري* (5 macamat) | c. 1108 | 85 KB |
| fa | Omar Khayyam | *رباعیات* (178 quatrains) | c. 1100 | 45 KB |
| fa | Saadi Shirazi | *گلستان* | 1258 | 188 KB |
| fa | Hafez Shirazi | *غزلیات* (first 50 ghazals) | c. 14th c. | 57 KB |

### Cluster E: Hellenic + Italic

| Locale | Author | Title | Year | Size |
|---|---|---|---|---|
| grc | Plato | *Ἀπολογία Σωκράτους* | Burnet 1903 ed. | 102 KB |
| el | Αλέξανδρος Παπαδιαμάντης | *Διηγήματα* | 1887-1906 | 287 KB |
| la | Publius Vergilius Maro | *Aeneis* | Greenough 1900 ed. | 494 KB |

### Cluster F: Sino-Tibetan + Japonic + Koreanic

| Locale | Author | Title | Year | Size |
|---|---|---|---|---|
| zh-Hans | Lu Xun | *狂人日记* | 1918 | 15 KB |
| zh-Hans | Compiled by Confucius's disciples | *论语* | c. 500 BCE | 67 KB |
| zh-Hans | Laozi | *道德经* (with Wang Bi 3rd-c. commentary) | c. 400 BCE | 89 KB |
| ja | Akutagawa Ryūnosuke | *羅生門* | 1915 | 17 KB |
| ja | Mori Ōgai | *舞姫* | 1890 | 48 KB |
| ja | Natsume Sōseki | *坊っちゃん / Botchan* | 1906 | 90 KB |
| ja | Terada Torahiko | *アインシュタイン* | 1921 | 12 KB |
| ja | Terada Torahiko | *茶わんの湯* | 1922 | 4 KB |
| zh-Hant | Sun Wu | *孫子兵法* | c. 500 BCE | 10 KB |
| zh-Hant | Zhu Ziqing | *背影* | 1925 | 2 KB |
| zh-Hant | 孫洙 (comp.) | *唐詩三百首* (both quatrain sections, 80 poems) | 1763 | 9 KB |
| zh-Hant | 蒲松齡 | *聊齋誌異* (5 tales) | 1766 | 36 KB |
| zh-Hans | 罗贯中 | *三国演义* (回 1-3) | 1522 | 47 KB |
| ko | Anonymous | *춘향가* (pansori edition) | c. 1850 | 139 KB |
| ko | Kim Sowol | *진달래꽃* (26-poem selection) | 1925 | 14 KB |
| ko | Heo Gyun | *홍길동전* 30-jang gyeongpan | early 19th c. ed. | 80 KB |
| ko | Lady Hyegyong (헌경왕후) | *한중록* (권일, the 1795 recension) | 1795 | 74 KB |
| ko | Yu Kilchun (유길준) | *서유견문* (서 + 제1편) | 1895 | 51 KB |

### Cluster G: Austroasiatic + Kra-Dai

| Locale | Author | Title | Year | Size |
|---|---|---|---|---|
| vi | Nguyễn Du | *Truyện Kiều* (opening 500 lines) | 1820 | 21 KB |
| vi | Nguyễn Đình Chiểu | *Lục Vân Tiên* | 1858 | 87 KB |
| vi | Hồ Xuân Hương | 22 Nôm poems | c. 1800 | 7 KB |
| th | Sunthorn Phu | *นิราศภูเขาทอง* | 1828 | 28 KB |
| th | Sunthorn Phu | *นิราศเมืองแกลง* | 1807 | 78 KB |
| th | Anonymous | *ขุนช้างขุนแผน* ตอนที่ ๑ | 1872 ed. | 43 KB |

### Cluster H: Niger-Congo

| Locale | Author | Title | Year | Size |
|---|---|---|---|---|
| sw | Mwana Kupona binti Msham | *Utendi wa Mwana Kupona* | 1858 | 9 KB |
| sw | Carl Velten (ed.) | *Safari za Wasuaheli* | 1901 | 406 KB |
| sw | Edward Steere | *Swahili Tales* | 1870 | 288 KB |
| sw | Mzee bin 'Ali bin Kidogo bin il-Qadiri | *Sha'iri la Makunganya* | 1898 | 8 KB |
| yo | Samuel Adjai Crowther | *A Vocabulary of the Yoruba Language* | 1852 | 521 KB |
| yo | Richard Edward Dennett | *My Yoruba Alphabet* | 1916 | 60 KB |
| yo | Thomas Jefferson Bowen | *Yoruba Proverbs* (Smithsonian) | 1858 | 16 KB |

### Cluster I: Iroquoian

| Locale | Author | Title | Year | Size |
|---|---|---|---|---|
| chr | Cherokee National Council | *Constitution of the Cherokee Nation* (1839, excerpted) | 1892 | 44 KB |

### Cluster J: Constructed languages (artificial auxiliary)

| Locale | Author | Title | Year | Size |
|---|---|---|---|---|
| eo | L. L. Zamenhof | *Fundamenta Krestomatio* | 1903 | 697 KB |
| vo | Various | *Penäds se Volapükagaseds* (gazette anthology, 268 pieces) | 1875-1901 | 397 KB |
| io | Various | *Nova Horizonti* (Ido literary magazine) | 1919 | 227 KB |
| io | Otto Jespersen | *Historio di nia linguo* | 1912 | 14 KB |

### Cluster K: Dravidian

| Locale | Author | Title | Year | Size |
|---|---|---|---|---|
| ta | Thiruvalluvar | *திருக்குறள் / Tirukkuṟaḷ* | c. 500 | 237 KB |
| ta | Subramania Bharati | *தேசிய கீதங்கள் / Tēciya Kītaṅkaḷ* | 1921 | 207 KB |
| ta | Various poets | *குறுந்தொகை / Kuṟuntokai* | c. 300 | 236 KB |

### Cluster L: Austronesian (Polynesian)

| Locale | Author | Title | Year | Size |
|---|---|---|---|---|
| haw | S. N. Haleole | *Ka Moolelo o Laieikawai* | 1918 | 293 KB |
| haw | Anonymous | *Ka Moolelo o Umi* | 1917 | 73 KB |
| mi | He kaitito maha (coll. George Grey) | *Ko Nga Moteatea, Me Nga Hakirara O Nga Maori* | 1853 | 79 KB |
| mi | Wiremu Maihi Te Rangikaheke (Grey, ed.) | *Ko Nga Mahinga a Nga Tupuna Maori* | 1854 | 108 KB |
| mi | Various tribal narrators (John White, ed.) | *Nga Kauhau Maori o Nehe* (Ancient History Vol. I, Maori part) | 1887 | 277 KB |

### Cluster M: English program (historical Englishes + regional world literature)

| Locale | Author | Title | Year | Size |
|---|---|---|---|---|
| ang | Anonymous | *Beowulf* (excerpt) | 1888 ed. | 45 KB |
| enm | Geoffrey Chaucer | *The Canterbury Tales* (General Prologue, Miller's Tale, Nun's Priest's Tale) | 1900 ed. | 97 KB |
| sco | Robert Burns | *Poems, Chiefly in the Scottish Dialect* (selection) | 1786 | 62 KB |
| en-GB | William Shakespeare | *Shake-speares Sonnets* (1609 Quarto spelling) | 1609 | 100 KB |
| en-US | Walt Whitman | *Leaves of Grass* (1855 first-edition text) | 1855 | 171 KB |
| en-IE | James Joyce | *Dubliners* | 1914 | 369 KB |
| en-CA | L. M. Montgomery | *Anne of Green Gables* | 1908 | 562 KB |
| en-CA | Stephen Leacock | *Sunshine Sketches of a Little Town* | 1912 | 320 KB |
| en-CA | E. Pauline Johnson | *Flint and Feather* | 1912 | 143 KB |
| en-NZ | Katherine Mansfield | *The Garden Party and Other Stories* | 1922 | 322 KB |
| en-ZA | Olive Schreiner | *The Story of an African Farm* | 1883 | 538 KB |
| en-AU | Henry Lawson | *While the Billy Boils* | 1896 | 452 KB |
| en-AU | A. B. Paterson | *The Man from Snowy River and Other Verses* (selection) | 1895 | 47 KB |
| en-IN | Sarojini Naidu | *The Golden Threshold* | 1905 | 46 KB |
| en-IN | Toru Dutt | *Ancient Ballads and Legends of Hindustan* | 1882 | 126 KB |
| en-IN | Rabindranath Tagore | *Gitanjali* (the author's 1912 English self-translation) | 1912 | 76 KB |
| en-JM | Claude McKay | *Constab Ballads* | 1912 | 61 KB |

### Cluster N: Turkic

| Locale | Author | Title | Year | Size |
|---|---|---|---|---|
| tr | Ömer Seyfettin | *Seçme Hikâyeler* (five stories) | 1917-1919 | 79 KB |

## Caveats and substitutions

A handful of locales needed a different source or a different pick than originally planned. The changes are documented here for transparency:

- **th** (primary): the locked primary *Phra Aphai Mani* (Sunthorn Phu) is not on th.wikisource; the closest digitised same-author canonical works (*Nirat Phukhao Thong* 1828, *Nirat Mueang Klaeng* 1807) were included instead. Third book *Khun Chang Khun Phaen* (1872 ed.) adds folk-epic register.
- **vi** (second): the originally-planned second pick (full *Truyện Kiều*) duplicated the same Wikisource source as the opening excerpt. Replaced with Nguyễn Đình Chiểu's *Lục Vân Tiên* (1858) for genre and author differentiation. Third book Hồ Xuân Hương 22-poem set adds an earlier-period female-voice register.
- **cy**: source for the first two books is the Edwards 1907 modernised Welsh edition. The `year` field reflects that; `year_note` records the medieval (12th-14th c.) manuscript origin. Third book *Manawydan uab Llyr* is Middle Welsh orthography (14th c. ms.) for register variety.
- **yo**: the originally-planned literary primary (I. B. Akinyele, *Iwe Itan Ibadan* 1911) is not digitised in clean form anywhere reachable. All three books here are reference works rather than literary prose, exercising the Yoruba script (ọ, ẹ, ṣ, tone marks): Crowther 1852 *Vocabulary*, Dennett 1916 *Primer*, Bowen 1858 *Proverbs* (the third pick adds 100 numbered proverbs as secular wisdom literature).
- **uk** (*Кобзарь*): the Shevchenko book follows the 1840 Saint Petersburg first edition exactly as it was printed, which means yaryzhka: the Russian-alphabet orthography that tsarist-era printing imposed on Ukrainian books. Preserving it is edition fidelity, the same principle that keeps the 1803 Polish orthography in *Treny*, the 1609 spelling in the Sonnets, and the unmacronised Hawaiian; the rows of dots reproduce the censor's cuts as the first edition's readers saw them. It is emphatically not a statement about how Ukrainian should be written. A parallel modern-orthography *Кобзар* edition (e.g. a scan-backed 1907 Domanytskyi-based text) would be a welcome addition, as would any scan-backed edition of *Лісова пісня* (see QUALITY.md). The cluster's other two books, *Лісова пісня* and *Тіні забутих предків*, are in modern Ukrainian orthography.
- **sw**: Velten *Safari za Wasuaheli* sourced from Internet Archive djvu.txt OCR, which carries visible noise. The Steere 1870 pick was re-sourced 2026-07-24 from the proofread multilingual-Wikisource transcription as the complete *Swahili Tales* (its earlier invented Swahili title was corrected to the printed one); the Utenzi wa Ayubu opening is excluded per the secular rule. Mwana Kupona's *Utendi* is the corpus's one book whose transmission base is a twentieth-century scholarly edition: africanpoems.net prints the text from J. W. T. Allen, *Tendi* (Heinemann, 1971), whose edited transcription may carry an editorial layer of its own even though the 1858 poem does not. Disclosed in the file's `source_note` from 2026-08-03 and flagged in QUALITY.md for re-sourcing from Alice Werner's 1917 edition in *Harvard African Studies*.
- **ko**: Kim Sowol *Jindallaekkot* is a curated 26-poem subset of the 126-poem 1925 collection (Wikimedia rate-limiting prevented full fetch). Heo Gyun *Hong Gildong-jeon* edition used here is the early 19th-c. Seoul woodblock rather than the c. 1612 original.
- **ur** (primary swap): Premchand-Urdu (the script-distinct counterpart to hi Premchand) was the original target but has no clean-text source on ur.wikisource, rekhta.org, or Internet Archive (Perso-Arabic Urdu OCR runs ~40% accuracy). Substituted with Ghalib *Divan* and Iqbal *Bang-e-Dara* (two canonical Urdu poets a century apart). Third book Mir Taqi Mir adds a third generation.
- **he** (third): Mendele *Sefer ha-Kabtsanim* not on he.wikisource; Ben-Yehuda API not exposed for programmatic access. Sholem Aleichem *Shoshana* (1888, Hebrew-language story) substituted.
- **pt-BR** (third): Aluísio Azevedo *O Cortiço* not on Gutenberg in clean Portuguese form. Bernardo Guimarães *A Escrava Isaura* substituted.
- **chr**: pre-1929 Cherokee-language corpus on Internet Archive is overwhelmingly missionary-religious. The 1839 *Constitution of the Cherokee Nation* (excerpted from the 1892 *Constitution and Laws*) is the substantive secular pick that emerged from a deep search; documented in frontmatter `selection_note` and `year_note`.
- **gd / es-MX**: taken from Internet Archive djvu.txt OCR. Quality is recognisable but noisy; OCR posture matches the documented sw-Velten precedent. A 2026-07-19 sweep looked for typed replacements: es.wikisource has neither *Los de abajo* nor *Tomóchic*, and no typed source surfaced for the gd pick, so these stand until better sources are digitised.
- **ga** (replaced 2026-07-19): *An crann géagach* was originally Internet Archive tesseract OCR of the cló Gaelach print, unreadable in places (Gaelic-type sigla and lowered-s shapes defeated the OCR). Replaced with the multilingual Wikisource typed transcription (13 stories, per-story ProofreadPage transclusions of the 1919 edition).
- **fr-CA** (primary, replaced 2026-07-19): the original *Les Anciens Canadiens* was Internet Archive OCR degraded beyond safe automated repair. Replaced wholesale with the fr.wikisource proofread transcription (TextQuality 100 percent, validated against the 1863 Desbarats et Derbishire first edition), including the author's *Notes et éclaircissements*. Second book *Angéline de Montbrun* (Laure Conan, 1884) added from Project Gutenberg.
- **tr**: pre-1929 Turkish was printed in the Ottoman Arabic script; the 1928 alphabet reform postdates nearly all of Ömer Seyfettin's publication history. The *Seçme Hikâyeler* here (five canonical stories: Kaşağı, Pembe İncili Kaftan, Falaka, Diyet, Başını Vermeyen Şehit; first published 1917-1919, author died 1920) uses tr.wikisource's modern Latin-script transliterations. The transliteration is an orthographic conversion of pre-1929 originals rather than a new work; documented in the file's `source_note`. A Chagatai or Ottoman-script (ota) pick remains welcome per the wishlist.
- **ar** (Alf Laylah wa-Laylah): ar.wikisource wraps the verse interludes in div blocks and renders the honorific ligature (U+FDFA) via the {{ص}} template; an early conversion dropped all 48 verse blocks and the ligature. Found by the 2026-07-14 upstream fidelity sweep, fixed in `convert-wikisource.py` (div unwrapping, glyph-template map), and the book regenerated with punctuation counts matching upstream exactly. Verse caesuras are preserved as non-breaking-space runs so they survive markdown rendering.
- **th**: th.wikisource typesets klon verse as two-column wak tables and per-line verse templates; conversion flattens each verse line (bat) to one markdown line with the caesura space preserved, so reading order is unchanged. Early conversions dropped the stanza-opening fongman marks (๏); found and fixed 2026-07-14, with `convert-wikisource.py` taught table rows, verse templates, and the section-mark family (๏ ๚ ๛), and both Sunthorn Phu poems verified to regenerate reproducibly from source (all fongman and paiyannoi counts match upstream). Stanza grouping beyond the fongman marks is not carried over.
- **pl**: years are first-printing dates while the texts here follow later editions, documented per file: *Pan Tadeusz* from the 1834 first edition (Księgi I-II excerpt, selection_note), *Treny* via the 1803 Mostowski edition, *Kamizelka* via the 1935 collected edition (the sole complete transcription on pl.wikisource; US public domain rests on the 1882 first publication). Where the source editions carried Wikisource correction templates, the displayed corrected reading is reproduced.
- **ta**: the Tirukkural is included under the ethical-wisdom-literature rule (the Gulistan and Analects precedent). Kural couplets carry the canonical 1-1330 numbering (the source etext's number typos are not reproduced), and one heading emendation (iyal 2.2, mislabeled in the etext against its own colophon) is applied via a disclosed converter flag. *Kuṟuntokai* is poems 1-376 per the source etext's coverage, with the invocatory verse omitted; both facts are declared in the file.
- **bn**: *Gitanjali* is devotional lyric poetry included as literary canon (the Hafez precedent, cited in the file's selection_note); the deliberate pick of *Kapalkundala* over *Anandamath* keeps clear of the sacred-text boundary. Texts follow proofread editions (the 1913 Bengali edition of the 1910 Gitanjali cycle; the 1870 second edition of the 1866 Kapalkundala). For these walked books verify-upstream passes structurally only (the top pages carry no body text); the fidelity evidence is exact unit-count matches against the source (157 songs / 16 / 32 chapters) and zero-duplication checks.
- **haw**: both books come from bilingual Bishop Museum editions; only the Hawaiian text is included, separated from the facing English mechanically. Period orthography is preserved (no consistent okina or kahako in the sources). OCR posture is the sw-Velten tier, documented per file; *Laieikawai* carries one disclosed systematic repair (OCR-mangled opening quotation marks restored via a converter flag; nothing else corrected).
- **mi**: attribution is corrected against the 1854 title page: the *Nga Mahinga* manuscripts were principally written by Wiremu Maihi Te Rangikaheke (with contributions from Henare Matene Te Whiwhi), published by George Grey as editor under his own name; the combined attribution and the per-legend uncertainty are recorded in the file. *Ko Nga Moteatea* is a first-100 selection of the 507-piece collection, retrieved from CDX-verified Wayback snapshots of the decommissioned NZETC host. Unmacronised 1850s orthography is preserved in both. Karakia appearing among the waiata are included as indigenous oral-literary canon; the secular rule excludes sacred texts rather than collected oral literature (the same reading that admits the cosmogony narratives and the Mabinogi).
- **writing-mode declarations** (ja, zh-Hant, zh-Hans, ko): works whose setting convention is vertical declare `writing-mode: vertical-rl` in the CSS value space: the three Meiji literary ja books (tategaki convention), the classical zh-Hant works (*孫子兵法*, *唐詩三百首*, *聊齋誌異*), the zh-Hans classics (*论语*, *道德经*, and the *三国演义* chapters; vertical setting remains common in modern simplified editions of the classics), and the classical ko works (the woodblock *홍길동전*, the *춘향가* pansori text, *한중록*, and the 1895 *서유견문*). Modern-vernacular works deliberately carry NO writing-mode field and read horizontally by default: the two Terada Torahiko science essays (ja), *狂人日记* (zh-Hans, May Fourth vernacular), *背影* (zh-Hant, 1925 vernacular essay), and *진달래꽃* (ko, 1925). The declared/absent split is itself deliberate: the field records a convention where one genuinely exists and stays silent where it does not, so consumers exercise both the honored-hint path and the default path. Portable frontmatter: vertical-capable renderers honor it, everything else ignores it.
- **verse line breaks** (corpus-wide convention, ratified 2026-07-17): verse lines within a stanza end with an exact two-space CommonMark hard break; stanzas and poems are separated by blank lines; hard-wrapped prose is left to merge, which is its correct rendering. This convention was retrofitted across the corpus after review found verse converted with bare soft newlines rendering as prose walls; the repair was whitespace-only and text-invariant except where noted. Two books are exceptions by design: the th poems and mi *Ko Nga Moteatea* use line-per-paragraph (each verse line blank-separated), an accepted airier style.
- **fa** (*گلستان*): the original conversion silently lost every embedded verse passage (the source subpages are ProofreadPage transclusion shells whose raw wikitext carries no body). Restored 2026-07-17 by full reconversion from the rendered edition: 606 verse blocks including بنی آدم, with the footnote apparatus (which itself contains variant verse) excluded.
- **en program** (ang, enm, sco, en-*): the historical entries require original spelling, and two picks were dropped rather than shipped modernised when that could not be verified: Bacon's 1625 *Essayes* (only modernised transcriptions exist) and Bradstreet's 1650 *The Tenth Muse* (surviving only as black-letter page images; a transcription is on the wishlist). en-IN carries Indians writing in English, the founding canon of that tradition; Anglo-Indian colonial writing is a different literature and deliberately not what the locale represents. en-JM's companion volume *Songs of Jamaica* (1912) is not cleanly transcribed anywhere and remains on the wishlist.
- **quality flags under review** (pre-publish; the full ledger with fix paths lives in [QUALITY.md](QUALITY.md)): *Volaspodel* (vo) was OCR-degraded beyond repair and was replaced 2026-07-25 by *Penäds se Volapükagaseds*, an anthology of 268 hand-typed gazette pieces (1875-1901) each carrying its printed source citation; the selection rules and exclusion counts are in the book's selection_note. On 2026-07-25 a two-engine re-OCR pipeline (see [REOCR.md](REOCR.md)) rebuilt five of these: *Tomóchic* (es-MX, from the better 1911 scan, 97% two-engine agreement, chapter V recovered), *Safari za Wasuaheli* (sw Velten, 99%, the systematic u-as-n corruption eliminated), *Ko Nga Mahinga* (mi, 99%), *Nova Horizonti* (io, 99%, article headings recovered), and the chr book, which was also narrowed to the 1839 *Constitution* alone (95%). All five carry `text_quality: noisy` or `alpha` and remain flagged pending a fluent read; none is yet a proofread edition. *Yoruba Proverbs* (yo Bowen) lost its subdot vowels and tone marks to the scan and seven of its hundred proverbs; the re-OCR recovers the diacritics but the engines diverge on Bowen's archaic orthography, so a Yoruba reader is still needed. (*Swahili Tales* (sw Steere) and both haw books cleared their flags on 2026-07-24: re-sourced wholesale from the proofread multilingual-Wikisource transcription and from Distributed Proofreaders Gutenberg transcriptions respectively, replacing Google Books and Internet Archive OCR. *Moladh Beinn-Dòrain* (gd) cleared its flag on 2026-07-20: re-sourced wholesale from the roman-type Calder 1912 edition with editorial accent restoration, replacing the unreadable 1848 Gaelic-type OCR. *Les Anciens Canadiens* (fr-CA) cleared its flag on 2026-07-19: the OCR-derived Internet Archive text was replaced wholesale by the fr.wikisource proofread transcription, validated at TextQuality 100% against the 1863 first edition.) The chr *Constitution* and the yo dictionaries have line-structured content (officer lists, dictionary entries) that current markdown structure does not fully express; documented as known limitations.
- **la** (*Aeneis*): the la.wikisource transcription names its edition as Greenough (Ginn, 1900) but does not reproduce Greenough's orthography. Two layers sit on top of it. Vowel-quantity macrons are carried throughout, which the print edition does not have; they come from The Latin Library, the route la.wikisource cites, whose Aeneid I is macronised and uses v. Its Books 2-12 are unmacronised and use v too, so the macronisation and the u-normalisation of Libri II-XII are both Wikisource's. The u/v convention is not uniform either: Liber I writes consonantal v (avena, venit) while Libri II-XII write u (renouare, uidi), so one file carries two conventions. Both layers are left exactly as transcribed. Normalising either one means deciding consonantal u from vocalic u word by word, which is an editorial act on the text and would be guesswork on my part. The inconsistency is flagged in QUALITY.md; a contributor who reads Latin could settle it. The bracketed line 10.872 and the Ille ego pre-proem are edition questions rather than transcription ones and are explained in the book's source_note.
- **el / grc** (Greek): the two are separate languages and separate locales here. Plato is Attic, so it sits under `grc`; Papadiamantis is modern Greek under `el`. Both texts are polytonic, which took choosing: most Greek digitisation of pre-1929 work converts to the monotonic system introduced in 1982, rewriting the accentuation of the original. The Papadiamantis converter refuses any story whose transcription carries no breathings, which is why the selection omits *Όνειρο στο κύμα*, available on el.wikisource only in monotonic form. *Το Μοιρολόγι της Φώκιας* is absent because el.wikisource does not carry it at all.
- **am** (Amharic): **dropped from v1**. No pre-1929 PD Amharic literary text is digitised in clean form. Documented as an open gap rather than filled with a rule-breaking placeholder; clean secular sources are especially welcome.

## Text-quality tiers

Most books carry no `text_quality` field, meaning their text meets the corpus's normal fidelity bar (a typed or proofread source, or OCR that was read and cleaned). Eight books currently fall below that bar and say so machine-readably, so a consumer can filter them with one line and a reader application can flag them. Each has a matching open flag in [QUALITY.md](QUALITY.md); the field and the ledger must agree. See [FRONTMATTER.md](FRONTMATTER.md) for the field definition.

- **`text_quality: alpha`** (known substantial problems, provisional): chr *Constitution of the Cherokee Nation* (machine OCR of syllabary, re-run through the two-engine pipeline; the book was narrowed 2026-07-25 to the 1839 Constitution alone, which reaches 95% body-line agreement, but it is still unverified by a fluent reader; see REOCR.md), yo Bowen *Yoruba Proverbs* (subdot vowels and tone marks lost to OCR; needs manual re-transcription).
- **`text_quality: noisy`** (unproofread OCR with disclosed residual noise, readable and structurally sound): sw Velten *Safari za Wasuaheli* (re-OCR'd to 99% body-line agreement, machine OCR not yet read by a Swahili speaker), es-MX *Tomóchic*, io *Nova Horizonti*, mi *Ko Nga Mahinga*, and the yo reference works Crowther *Vocabulary* and Dennett *My Yoruba Alphabet*.

Books graduate out of the tiers as they are repaired or re-sourced; sw Steere, both haw books, gd, and fr-CA all did so in July 2026 and carry no tag.

## Conversion tooling

All conversion happens via scripts under `scripts/`:

| Script | Source family | Used for |
|---|---|---|
| `convert-gutenberg.py` | Project Gutenberg plain text | de-DE, de-AT, es-ES, fr, fi, is (Cluster A and seconds); Goethe Werther; Voltaire Candide; pt-PT Garrett; pt-BR Guimarães |
| `convert-wikisource.py` | Wikisource wikitext | ru, vi, th, cy, fi second, others |
| `convert-wikisource-html.py` | MediaWiki HTML with variant negotiation | zh-Hans (variant=zh-cn), Italian transclusion model |
| `convert-aozora.py` | Aozora Bunko Shift-JIS XHTML | ja Akutagawa, Mori Ōgai, Sōseki, Terada |
| `convert-rtl-sources.py` | Ben-Yehuda + Ganjoor.net + Wikisource ProofreadPage | he, fa |
| `convert-sagadb.py` | sagadb.org plain text | is Hrafnkels, Brennu-Njáls, Eyrbyggja |
| `convert-internet-archive.py` | Internet Archive djvu.txt OCR (language-agnostic) | yo, sw Velten, ga, gd, chr, es-MX Tomóchic |
| `convert-velten-safari.py` | IA-specific Velten 1901 cleanup | sw Velten |
| `convert-mwana-kupona.py` | africanpoems.net | sw Mwana Kupona |
| `convert-archive-djvu.py` | IA djvu.txt (used for Azuela) | es-MX Azuela |
| `convert-wikisource-collection.py` | Wikisource collection-index walker | es-MX Nervo *Perlas negras* |
| `convert-el-zarco.py` | Wrapper over the collection walker: es.wikisource chapter walk plus nav-line strip and named chapter headings | es-MX *El Zarco* |
| `convert-io-historio.py` | Multilingual-Wikisource single-page typed transcription | io Jespersen |
| `convert-makunganya.py` | Multilingual-Wikisource stanza-numbered verse | sw Makunganya |
| `convert-volapuk-anthology.py` | Category walk over the typed Volapük gazette items; Fonät-cited pre-1929 pieces only, chronological, secular and apparatus screens disclosed | vo anthology |
| `convert-white-kauhau.py` | NZETC TEI-HTML via Wayback raw snapshots, Maori-part extraction | mi White Vol. I |
| `convert-iqbal-bang-e-dara.py` | ur.wikisource Iqbal author-page section slicer | ur Iqbal |
| `convert-ghalib-divan.py` | Multi-level walk of Divan-e-Ghalib | ur Ghalib |
| `convert-wikisource-proofread-div.py` | pl.wikisource ProofreadPage layout (presentation-table body, display:none correction spans) | pl (all three) |
| `convert-uk-wikisource.py` | uk.wikisource three-shape converter: ProofreadPage verse with page-turn joins and censorship dot-rows (Кобзарь 1840), ProofreadPage prose with glossary notes (Коцюбинський), typed poem-block wikitext (Леся Українка) | uk (all three) |
| `convert-la-wikisource.py` | la.wikisource twelve-subpage walk over one `<poem>` block per book; drops the `{{versus}}` marginal line numbers, keeps book divisions as headings, and matches canonical line count | la *Aeneis* |
| `convert-madurai.py` | Project Madurai etext, Tirukkural structure | ta *Tirukkural* |
| `convert-madurai-anthology.py` | Project Madurai Sangam anthology layout | ta *Kuṟuntokai* |
| `convert-bharati.py` | Wrapper over the collection walker for ta.wikisource poetry sub-pages | ta Bharati |
| `convert-bn-proofread.py` | bn.wikisource ProofreadPage sub-page walker | bn (all three) |
| `convert-hawaiian-bilingual.py` | IA bilingual-edition language separation (consonant-ratio scoring) | haw (superseded 2026-07-24 by the Gutenberg re-source) |
| `convert-haw-gutenberg.py` | PG plain text, Hawaiian-section slicing (Laieikawai MOKUNA X heading restored by English-chapter alignment; Umi genealogy set as a table) | haw (both) |
| `convert-steere-wikisource.py` | Multilingual-Wikisource ProofreadPage walk over the 22 secular pieces in printed order (reuses the uk walker) | sw Steere |
| `convert-nzetc.py` | NZETC sections via Wayback CDX resolution | mi *Ko Nga Moteatea* |
| `convert-grey-mahinga.py` | IA djvu single-work extraction for the 1854 *Nga Mahinga* | mi *Nga Mahinga* |
| `convert-gulistan.py` | fa.wikisource rendered-HTML walk with beyt-span verse extraction | fa *گلستان* (restored) |
| `convert-tangshi-selection.py` | zh.wikisource per-poem index walk, multi-tradition page resolution | zh-Hant *唐詩三百首* |
| `convert-liaozhai-tales.py` | Per-volume tale slicing, critical-edition apparatus stripped (disclosed) | zh-Hant *聊齋誌異* |
| `convert-sanguo-chapters.py` | Simplified-variant chapter assembly | zh-Hans *三国演义* |
| `convert-ko-vertical.py` | ko.wikisource dual-route (wikitext + rendered) with ko chrome stripping | ko *한중록*, *서유견문* |
| `convert-chaucer-skeat.py` | Skeat-text Middle English extraction | enm |
| `convert-burns-kilmarnock.py` | Kilmarnock-edition Scots selection | sco |
| `convert-shakespeare-sonnets-1609.py` | 1609 Quarto original-spelling transcription | en-GB |
| `convert-whitman-1855.py` | 1855 first-edition text | en-US |
| `convert-mckay-constab.py` | en.wikisource ballad walk, dialect verbatim | en-JM |
| `convert-krestomatio.py` | Project Gutenberg #8224 (Fundamenta Krestomatio) selection | eo |
| `convert-chr-reocr.py` | Two-engine re-OCR assembly from the local scan cache (see [REOCR.md](REOCR.md)); 1839 Constitution excerpt with recovered article headings | chr |
| `convert-velten-reocr.py` | Two-engine re-OCR assembly from the local scan cache (see [REOCR.md](REOCR.md)); six Swahili narratives | sw Velten |
| `convert-tomochic-reocr.py` | Two-engine re-OCR ([REOCR.md](REOCR.md)) over the 1911 scan; Roman-numeral chapters | es-MX Tomóchic |
| `convert-ngamahinga-reocr.py` | Two-engine re-OCR ([REOCR.md](REOCR.md)); nine-story Part-I excerpt, all-caps titles | mi Nga Mahinga |
| `convert-nova-reocr.py` | Two-engine re-OCR ([REOCR.md](REOCR.md)); all-caps article headings | io Nova Horizonti |
| `convert-crowther-reocr.py` | Two-engine re-OCR ([REOCR.md](REOCR.md)); dictionary entry detection, diacritic recovery | yo Crowther |
| `apply-verse-hardbreaks.py` | Whitespace-only verse hard-break repair (blanket / block-classified / region modes, non-whitespace invariance gate) | line-break campaign |
| `format-corpus-md.py` | Post-conversion formatting pass (frontmatter-invariant) | en program |
| `check-verse-breaks.py` | Detector for soft-wrapped verse (runs of short unbroken lines) | contributor gate |
| `lint-corpus.py` | Validation pass over the corpus | all directories |

Each script accepts `--help` for invocation details. All write the YAML-frontmatter + body markdown structure documented at the top of this file.

## Linguistic and script-family coverage

The corpus covers:

**Language families**:
- Indo-European: Germanic (de-DE, de-AT, nl, sv, no, sco, English: en-GB, en-US, en-IE, en-CA, en-NZ, en-ZA, en-AU, en-IN, en-JM, plus the historical stages ang and enm), Romance (es-ES, es-MX, fr, it, pt-PT, pt-BR), Slavic (ru, uk, pl, cs), Indo-Iranian (hi, bn, fa, ur), Celtic (cy, ga, gd), Hellenic (grc, el), Italic (la), Old Norse (is)
- Afro-Asiatic: Semitic (he, ar)
- Sino-Tibetan: Sinitic (zh-Hans, zh-Hant)
- Japonic: Japanese (ja)
- Koreanic: Korean (ko)
- Austroasiatic: Vietnamese (vi)
- Kra-Dai: Thai (th)
- Niger-Congo: Bantu (sw), Yoruboid (yo)
- Iroquoian: Cherokee (chr)
- Uralic: Finnic (fi)
- Turkic: Turkish (tr)
- Dravidian: Tamil (ta)
- Austronesian: Polynesian (haw, mi)

**Script systems**:
- Latin (with rich variant accents per locale)
- Cyrillic (ru, uk)
- Ancient Greek (grc), Modern Greek (el)
- Hebrew (he)
- Arabic + Perso-Arabic (ar, fa, ur)
- Devanagari (hi)
- CJK (Han / kana / Hangul: zh-Hans, zh-Hant, ja, ko)
- Thai abugida (th)
- Cherokee syllabary (chr, U+13A0-U+13FF + U+AB70-U+ABBF)
- Tamil script (ta)
- Bengali script (bn)

**Documented gaps** (locales considered and deliberately left open rather than force-filled; the Amharic pattern):

- **tr** (Turkish): the 1928 alphabet reform means pre-1929 public-domain Turkish in modern Latin orthography barely exists; the pre-reform literature is Ottoman Turkish in Arabic script, which would be its own locale (ota) and a worthwhile future addition on its own terms.
- **mn** (Mongolian): the pre-1929 corpus is classical Mongolian in the traditional vertical script; clean digitised secular sources are scarce (Mongolian Wikisource has no full subdomain), and vertical layout raises rendering questions markdown tooling does not answer today. Further facts recorded 2026-07-16: macOS ships no Mongolian-script font (a free remedy exists: Noto Sans Mongolian, SIL OFL, installable or bundleable); Mongolian is vertical-lr, a distinct writing mode from the CJK vertical-rl that vertical-capable renderers implement first; and the digitised classical-script texts that do exist (the Ritsumeikan/National University of Mongolia TEI edition of the Altan Tobchi, and the TMSDL digital library's chronicles) are research prototypes with no stated license, which fails this corpus's provenance bar. The most promising path is asking those scholars to release one chronicle under an open license; a contributor with the connections is warmly invited.
- **iu** (Inuktitut), **cop** (Coptic): the pre-1929 digitised corpora are overwhelmingly missionary Bible translation and liturgical material, which the secular rule excludes; the Cherokee Constitution precedent shows a substantive secular find can reopen either.

**Still missing for v1.2+**: a transcription of Anne Bradstreet's *The Tenth Muse* (1650; only black-letter page images survive online, and the corpus dropped the pick rather than ship modern spelling), Claude McKay's *Songs of Jamaica* (1912; untranscribed anywhere clean), English-variant locales per the stop rule below (named candidates: en-GH via Casely Hayford's *Ethiopia Unbound* 1911, en-PH via Galang's *A Child of Sorrow* 1921), Tibetan (a new script system with strong secular candidates: the Gesar folk epic and the songs of Tsangyang Gyatso, both with pre-1929 woodblock fixations; macOS ships the Kailasa face, so rendering is ready), Telugu and other Dravidian languages beyond Tamil, more Slavic Latin variants beyond Polish and Czech, classical literary Turkic (Chagatai, and Kazakh's Arabic-script Abai editions of 1909) to complement the post-reform Turkish here (see the tr caveat above), Mongolic, more Indigenous American (Cree, Inuktitut), Coptic, Ottoman Turkish (ota), Hiiakaikapoliopele in Hawaiian (the 1905-06 serial lives in the nupepa/ulukau newspaper archives, not Internet Archive; a contributor with access could bring the great Hiiaka epic here).

**English-variant stop rule**: an English-variant locale enters when a pre-1929 literature genuinely exists there and the entry is founding-canon or orthographically distinct; territories whose anglophone literatures bloomed later (Singapore, Nigeria, Kenya) are not gaps, their literatures simply post-date the corpus's line.

## Acknowledgements

Building this corpus depended on the labour of many people who digitised, transcribed, proofread, and made these texts available. Especially:

- The Project Gutenberg volunteers and the PG Distributed Proofreading Team
- The per-language Wikisource volunteer communities, especially the Welsh, Vietnamese, Thai, Chinese, Hindi, Hebrew, Persian, Urdu, Russian, Greek, and Italian editor groups
- Aozora Bunko's volunteers for Japanese classical and modern literature
- Project Ben-Yehuda for the canonical Hebrew literature archive
- The Ganjoor.net project for Persian classical poetry
- The Saga Database team for Icelandic medieval prose
- The Internet Archive and Google Books for scanning items unavailable elsewhere (Yoruba, Swahili, Cherokee, Mexican Spanish, Irish, Scots Gaelic)
- Matt Schmitt for the [`mlschmitt/classic-books-markdown`](https://github.com/mlschmitt/classic-books-markdown) repo that motivated and informed this work
