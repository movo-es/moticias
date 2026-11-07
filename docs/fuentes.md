# MOTICIAS · Inventario de fuentes (edición nº 1, 4 de noviembre de 2026)

Fuentes de libre acceso verificadas el 4-11-2026 (carga directa de la URL y, cuando existe, del RSS o la API). Las no verificadas se marcan. Orden: primero lo primario (boletines, contratación, reguladores), después asociaciones y prensa. El barrido diario usa la API del BOE (`https://www.boe.es/datosabiertos/api/boe/sumario/AAAAMMDD`, cabecera `Accept: application/json`) y los RSS listados. La versión legible por máquina (sin las notas) es `portal/data/sources.json`.

Mantenimiento: la rutina diaria anota aquí (sección «Cambios detectados») toda fuente que deje de responder, cambie de dominio o de feed, el día en que lo detecta.

## Boletines oficiales (20)

- **BOA – Boletín Oficial de Aragón** — transversal/autonómico · diaria (lunes a viernes)
  https://www.boa.aragon.es/
  Disposiciones y anuncios del Gobierno de Aragón; concesiones y licitaciones de transporte.
  Nota: HTTP 200; portal tipo aplicación JS (poco texto rastreable). Listado por fecha: /cgi-bin/EBOA/BRSCGI?CMD=VERLST&BASE=BOLE&SEC=FIRMA&DOCS=1-200 (200 OK). Sin RSS localizado.
- **BOC – Boletín Oficial de Canarias** — transversal/autonómico · diaria (lunes a viernes)
  https://www.gobiernodecanarias.org/boc/
  Disposiciones de la Consejería de Obras Públicas, Vivienda y Movilidad, Cabildos (transporte insular) y anuncios.
  Nota: La página /boc/rss/ anuncia feeds (all.rss, consejeria/obras_publicas.rss, cabildo/*.rss) pero todos devolvían 404 el 04/11/2026; reintentar más adelante.
- **BOCCE (Ceuta) y BOME (Melilla)** — transversal/autonómico · BOME: martes y viernes; BOCCE: martes y viernes
  https://bomemelilla.es/
  Boletines de las ciudades autónomas: ordenanzas de movilidad, transporte urbano, puertos y anuncios.
  Nota: BOME verificado por WebFetch (suscripción por correo, sin RSS). BOCCE https://www.ceuta.es/ceuta/bocce NO verificado (conexión cerrada / robots).
- **BOCM – Boletín Oficial de la Comunidad de Madrid** — transversal/autonómico · diaria (lunes a sábado)
  https://www.bocm.es/
  Disposiciones de la Consejería de Vivienda, Transportes e Infraestructuras y del CRTM; anuncios y licitaciones.
  RSS/API: https://www.bocm.es/ultimo-boletin.xml
  Nota: Otros feeds: https://www.bocm.es/boletines.rss y https://www.bocm.es/sumarios.rss (página /rss verificada).
- **BOCYL – Boletín Oficial de Castilla y León** — transversal/autonómico · diaria (lunes a viernes)
  https://bocyl.jcyl.es/
  Disposiciones de la Consejería de Movilidad y Transformación Digital; anuncios y licitaciones.
  Nota: Portada verificada por WebFetch. Índice de feeds RSS en https://bocyl.jcyl.es/indiceRss.do (no pudo abrirse desde este entorno: conexión cerrada / robots).
- **BOE – Boletín Oficial del Estado (diario)** — transversal/ES · diaria (lunes a sábado)
  https://www.boe.es/diario_boe/
  Leyes, reales decretos, órdenes TMA/TED, convocatorias, anuncios de licitación y adjudicación (Sección V.A) y concesiones de transporte.
  RSS/API: https://www.boe.es/rss/boe.php
  Nota: RSS por secciones (?s=1, ?s=3, ?s=5A). Canal temático 'Transportes y tráfico': https://www.boe.es/rss/canal_leg.php?l=l&c=132 ; anuncios CPV servicios de transporte: https://www.boe.es/rss/canal_cpv.php?l=a&c=600 (ambos verificados).
- **BOE – Datos Abiertos (API sumario diario y legislación consolidada)** — transversal/ES · diaria
  https://www.boe.es/datosabiertos/
  API REST: sumario diario del BOE y del BORME en XML/JSON, legislación consolidada y datos auxiliares (departamentos, materias).
  RSS/API: https://www.boe.es/datosabiertos/api/boe/sumario/{aaaammdd}
  Nota: Requiere cabecera Accept: application/json (o application/xml). Probado con /api/boe/sumario/20261103 → 200 OK. Doc: https://www.boe.es/datosabiertos/documentos/APIsumarioBOE.pdf
- **BOIB – Butlletí Oficial de les Illes Balears** — transversal/autonómico · martes, jueves y sábado (más extraordinarios)
  https://www.caib.es/eboibfront/
  Disposiciones de la Conselleria d'Habitatge, Territori i Mobilitat y Consells Insulars; anuncios y licitaciones.
  RSS/API: https://www.caib.es/eboibfront/es/rss
  Nota: Feed RSS verificado (application/rss+xml). Robots bloquea WebFetch; HTTP 200 confirmado.
- **BOJA – Boletín Oficial de la Junta de Andalucía** — transversal/autonómico · diaria (lunes a viernes)
  https://www.juntadeandalucia.es/eboja.html
  Disposiciones y anuncios de la Consejería de Fomento, Articulación del Territorio y Vivienda; concesiones de transporte interurbano y licitaciones.
  RSS/API: https://www.juntadeandalucia.es/boja/distribucion/s51.xml
  Nota: Feed s51 = Sección 1 Disposiciones generales; s53 = Otras disposiciones (verificado). Sin feed por consejería.
- **BON – Boletín Oficial de Navarra** — transversal/autonómico · diaria (lunes a viernes) · **sin verificar**
  https://bon.navarra.es/es/ultimo-boletin
  Disposiciones del Gobierno de Navarra en transporte y movilidad; anuncios y licitaciones.
  Nota: NO verificado: el host cierra la conexión desde este entorno y robots bloquea WebFetch. Comprobar manualmente desde navegador.
- **BOPA – Boletín Oficial del Principado de Asturias** — transversal/autonómico · diaria (lunes a sábado) · **sin verificar**
  https://sede.asturias.es/bopa
  Disposiciones y anuncios del Principado; transporte y movilidad (CTA).
  Nota: NO verificado: el host cierra la conexión desde este entorno y robots bloquea WebFetch.
- **BOPV – Boletín Oficial del País Vasco** — transversal/autonómico · diaria (lunes a viernes)
  https://www.euskadi.eus/web01-bopv/es/bopv2/datos/Ultimo.shtml
  Disposiciones del Departamento de Movilidad Sostenible y de las Diputaciones Forales; anuncios de transporte.
  RSS/API: https://www.euskadi.eus/bopv2/datos/Ultimo.xml
  Nota: Feed RSS del último boletín verificado (XML válido). Sumario n.º 210 del 03/11/2026 visible.
- **BOR – Boletín Oficial de La Rioja** — transversal/autonómico · diaria (lunes a viernes)
  https://ias1.larioja.org/boletin/Bor_Boletin_visor_Servlet
  Disposiciones y anuncios del Gobierno de La Rioja; transporte interurbano y licitaciones.
  Nota: Visor del boletín responde 200; la portada https://web.larioja.org/bor-portada cierra la conexión desde este entorno. Sin RSS localizado.
- **BORM – Boletín Oficial de la Región de Murcia** — transversal/autonómico · diaria (lunes a sábado)
  https://www.borm.es/
  Disposiciones y anuncios de la Consejería de Fomento e Infraestructuras; concesiones y licitaciones.
  Nota: Verificado por WebFetch (sede electrónica del BORM). El feed /servicios/rss/borm.rss está bloqueado por WAF para clientes no navegador.
- **BORME – Boletín Oficial del Registro Mercantil** — transversal/ES · diaria (lunes a viernes)
  https://www.boe.es/diario_borme/
  Actos inscritos (constituciones, ceses, concursos, fusiones) de empresas de transporte; útil para movimientos empresariales.
  RSS/API: https://www.boe.es/rss/borme.php
  Nota: API: https://www.boe.es/datosabiertos/api/borme/sumario/{aaaammdd} (probada 20261103 → 200). Relevancia selectiva: filtrar por CNAE/objeto social.
- **DOE – Diario Oficial de Extremadura** — transversal/autonómico · diaria (lunes a viernes)
  https://doe.juntaex.es/
  Disposiciones de la Consejería de Infraestructuras, Transporte y Vivienda; anuncios y licitaciones.
  RSS/API: https://doe.juntaex.es/rss/rss.php?seccion=6
  Nota: seccion=6 = sumario completo; seccion=1 disposiciones generales; seccion=5 anuncios (página /rss/ verificada).
- **DOG – Diario Oficial de Galicia** — transversal/autonómico · diaria (lunes a viernes) · **sin verificar**
  https://www.xunta.gal/diario-oficial-galicia
  Disposiciones de la Consellería de Presidencia, Xustiza e Deportes / Mobilidade; anuncios y licitaciones.
  Nota: NO verificado: el servidor devolvió HTTP 500 en todas las rutas probadas el 04/11/2026. Reintentar.
- **DOGC – Diari Oficial de la Generalitat de Catalunya** — transversal/autonómico · diaria (lunes a viernes)
  https://dogc.gencat.cat/es/
  Normativa y anuncios del Departament de Territori; concesiones, ATM, licitaciones de transporte.
  Nota: HTTP 200 verificado; contenido no inspeccionado (robots bloquea WebFetch). Suscripciones por correo en /es/serveis/subscripcions/. Sin RSS público localizado.
- **DOGV – Diari Oficial de la Generalitat Valenciana** — transversal/autonómico · diaria (lunes a viernes)
  https://dogv.gva.es/es/
  Normativa y anuncios de la Conselleria de Medio Ambiente, Infraestructuras y Territorio; concesiones y licitaciones de transporte.
  Nota: Verificado por WebFetch. Alertas por correo: https://dogv.gva.es/es/alertas-del-diari-oficial. Sin RSS localizado.
- **DOUE / EUR-Lex – Diario Oficial de la Unión Europea** — transversal/UE · diaria
  https://eur-lex.europa.eu/oj/direct-access.html
  Reglamentos, directivas y decisiones de transporte (series L y C); vista diaria del DO y texto consolidado.
  Nota: Vista diaria serie L: https://eur-lex.europa.eu/oj/daily-view/L-series/default.html (verificada). EUR-Lex ofrece RSS predefinidos y personalizados, pero la página de ayuda RSS respondió 202 (reto anti-bot) y no pudo verificarse; alternativa: SPARQL/Cellar.

## Contratación pública y licitaciones (3)

- **Plataforma de Contratación del Sector Público (PLACSP)** — transversal/ES · continua (Atom actualizado varias veces al día)
  https://contrataciondelestado.es/wps/portal/plataforma
  Licitaciones, adjudicaciones y formalizaciones de todo el sector público estatal y plataformas agregadas (CC. AA., EE. LL.).
  RSS/API: https://contrataciondelestado.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom
  Nota: Atom verificado (13,5 MB, 459 entradas, updated 2026-11-03T20:13). Plataformas agregadas: /sindicacion/sindicacion_1044/PlataformasAgregadasSinMenores.atom. Datos abiertos mensuales (CODICE) y OpenPLACSP: https://www.hacienda.gob.es/es-ES/GobiernoAbierto/Datos%20Abiertos/Paginas/licitaciones_plataforma_contratacion.aspx
- **Plataforma de Serveis de Contractació Pública (Catalunya)** — transversal/autonómico · continua
  https://contractaciopublica.cat/es/inici
  Licitaciones de la Generalitat, ATM, FGC, TMB y entes locales catalanes (muchas no replicadas en PLACSP).
  Nota: HTTP 200 verificado. Ejemplo de plataforma regional distinta; otras CC. AA. (Euskadi, Galicia, Andalucía) vuelcan también en PLACSP vía agregación.
- **TED – Tenders Electronic Daily** — transversal/UE · diaria (lunes a viernes)
  https://ted.europa.eu/es/
  Anuncios de contratación pública europea (suplemento del DOUE): servicios de transporte, material rodante, concesiones.
  RSS/API: https://api.ted.europa.eu/v3/notices/search
  Nota: API POST verificada con consulta CPV 60100000 + ESP (JSON OK). Docs: https://docs.ted.europa.eu/api/latest/index.html. La página de RSS personalizados (/en/rss) responde 202 (reto anti-bot) y no pudo verificarse.

## Ministerios y reguladores (11)

- **AESA – Agencia Estatal de Seguridad Aérea – Notas de prensa** — aire/ES · semanal
  https://www.seguridadaerea.gob.es/es/quienes-somos/comunicacion/notas-de-prensa
  Notas de prensa, informes de actividad, resoluciones sobre derechos de pasajeros, drones y seguridad operacional.
  Nota: Verificado (23/10/2026: Informe General de Actividad 2025). La ruta /es/rss devuelve página de error del WAF.
- **Dirección General de la Marina Mercante (MITMS – área marítima)** — mar/ES · según publicación
  https://www.transportes.gob.es/maritimo
  Normativa y trámites de marina mercante: líneas de interés público, bonificaciones, titulaciones, seguridad marítima, derechos de pasajeros.
  Nota: Verificado por WebFetch. Novedades normativas aparecen vía BOE y participación pública (ver buscador MITMS).
- **OMI / IMO – Media Centre** — mar/internacional · según reuniones (mensual)
  https://www.imo.org/en/mediacentre/pages/default.aspx
  Resultados de comités (MEPC, MSC), convenios, medidas de descarbonización y seguridad marítima.
  Nota: Verificado por WebFetch (Media Centre). Press briefings: https://www.imo.org/en/mediacentre/pressbriefings/pages/default.aspx (200; robots bloquea WebFetch). Sin RSS.
- **DGT – Dirección General de Tráfico – Notas de prensa** — tierra/ES · varias por semana
  https://www.dgt.es/comunicacion/notas-de-prensa/
  Notas de prensa sobre operaciones especiales, siniestralidad, normativa de tráfico y vehículos, campañas.
  Nota: Verificado (29/10/2026: previsión Todos los Santos). Sin RSS localizado (/rss, /feed → 404).
- **CNMC – Comisión Nacional de los Mercados y la Competencia (ferroviario y aeroportuario)** — transversal/ES · varias por semana
  https://www.cnmc.es/sectores-que-regulamos/ferroviario
  Resoluciones, informes de supervisión (cánones Adif, tarifas Aena/DORA, mercado ferroviario de viajeros), expedientes de competencia en transporte.
  RSS/API: https://www.cnmc.es/feed/all
  Nota: Feed general verificado (application/rss+xml); no existe feed por sector. Aeroportuario: https://www.cnmc.es/sectores-que-regulamos/aeroportuario
- **Comisión Europea – 'Have your say' (iniciativas de transporte)** — transversal/UE · continua
  https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives_en?topic=TRANSPORT
  Consultas públicas, hojas de ruta y actos delegados de transporte abiertos a comentarios.
  Nota: HTTP 200 verificado; listado cargado por JS (WebFetch solo ve metadatos). Sin RSS; la página permite suscripción por correo con cuenta EU Login.
- **Comisión Europea – DG MOVE (Movilidad y Transportes) – Noticias** — transversal/UE · diaria
  https://transport.ec.europa.eu/news-events/news_en
  Noticias y propuestas legislativas, consultas, financiación CEF, informes; 'EU Transport in Figures' (Statistical Pocketbook).
  RSS/API: https://transport.ec.europa.eu/node/2/rss_en
  Nota: RSS verificado ('Mobility and Transport | News'). Pocketbook 2025: https://transport.ec.europa.eu/facts-funding/studies-data/eu-transport-figures-statistical-pocketbook_en (200).
- **Consejo de la UE – Formación Transporte, Telecomunicaciones y Energía (TTE)** — transversal/UE · Consejos de Transportes ~2 por semestre; comunicados continuos
  https://www.consilium.europa.eu/en/council-eu/configurations/tte/
  Agendas, resultados y comunicados de los Consejos de Transportes; orientaciones generales y acuerdos con el PE.
  Nota: Verificado por WebFetch (programa de la presidencia irlandesa). El sitio devuelve 403 a clientes no navegador; el filtro ?filters=2031 de notas de prensa no es específico de transporte.
- **MITMS – Buscador de participación pública (consulta previa / audiencia e información pública)** — transversal/ES · continua (2.665 expedientes acumulados)
  https://www.transportes.gob.es/ministerio/buen-gobierno/participacion-publica/buscador
  Proyectos normativos en consulta previa y audiencia pública (Marina Mercante, Carreteras, Ferroviario, Aviación Civil) con fechas de inicio y fin.
  Nota: Verificado: última entrada 29/10/2026 (RD que modifica el Reglamento de navegación marítima, plazo hasta 24/11/2026). Fuente clave para anticipar regulación.
- **Ministerio de Transportes y Movilidad Sostenible – Sala de prensa** — transversal/ES · diaria
  https://www.transportes.gob.es/ministerio/comunicacion/sala-prensa
  Notas de prensa diarias: acuerdos del Consejo de Ministros, licitaciones de obra, concesiones, nombramientos, declaraciones del ministro.
  Nota: Verificado (03/11/2026: autorizaciones A-4, A-23, Puerto de Málaga). Sin RSS; paginación ?page=N (scraping sencillo).
- **Parlamento Europeo – Comisión TRAN** — transversal/UE · semanal
  https://www.europarl.europa.eu/committees/en/tran/home/highlights
  Votaciones, informes, audiencias y notas de prensa de la Comisión de Transportes y Turismo.
  RSS/API: https://www.europarl.europa.eu/rss/committee/tran/en.xml
  Nota: RSS verificado ('TRAN - European Parliament', pubDate 03/11/2026). Nota: con user-agent de navegador el feed devolvió 403; con cliente simple, 200.

## Agencias y gestores de infraestructuras (9)

- **Aena – Notas de prensa y estadísticas mensuales de tráfico** — aire/ES · notas: varias por semana; estadísticas: mensual (~día 10-12)
  https://www.aena.es/es/corporativa/prensa/notas-de-prensa-y-fotonoticias.html
  Notas de prensa (resultados, tarifas, inversiones DORA) y estadísticas mensuales de pasajeros, operaciones y carga por aeropuerto (PDF/XLS).
  Nota: Verificado (28/10/2026: beneficio 9M 2026). Estadísticas: https://www.aena.es/es/estadisticas/informes-mensuales.html (último mes: septiembre 2026). Sin RSS.
- **EASA – Agencia de la UE para la Seguridad Aérea – Noticias** — aire/UE · semanal
  https://www.easa.europa.eu/en/newsroom-and-events/news
  Reglamentación aérea, directivas de aeronavegabilidad, Easy Access Rules, drones, informes de seguridad.
  RSS/API: https://www.easa.europa.eu/en/newsroom-and-events/news/feed.xml
  Nota: RSS verificado (redirige desde /rss.xml). Última noticia 16/10/2026.
- **ENAIRE – Noticias** — aire/ES · semanal
  https://www.enaire.es/sala_de_prensa/noticias
  Notas de prensa del gestor de navegación aérea: tráfico gestionado, U-space/drones, inversiones, retrasos ATC.
  Nota: Verificado (15/10/2026: U-space en Benidorm). Sin RSS.
- **EUROCONTROL – Newsroom** — aire/UE · diaria (datos) / semanal (noticias)
  https://www.eurocontrol.int/newsroom
  Datos de tráfico aéreo europeo (daily traffic, European Aviation Overview), previsiones, retrasos ATFM, publicaciones.
  RSS/API: https://www.eurocontrol.int/rss.xml
  Nota: RSS verificado. Última noticia 03/11/2026 (app FlyingGreen).
- **EMSA – Agencia Europea de Seguridad Marítima – Latest news** — mar/UE · semanal
  https://www.emsa.europa.eu/newsroom/latest-news.html
  Noticias, informes de seguridad marítima (EMSAFE), descarbonización, inspección de buques, servicios de vigilancia.
  RSS/API: https://www.emsa.europa.eu/newsroom/latest-news.html?format=feed&type=rss
  Nota: RSS verificado (Joomla, 'Latest News - EMSA').
- **Puertos del Estado – Estadísticas de tráfico portuario y comunicación** — mar/ES · estadísticas: mensual; noticias: semanal
  https://www.puertos.es/datos/estadisticas/mensuales
  Resúmenes mensuales de tráfico (toneladas, TEU, pasajeros, cruceros) por autoridad portuaria en XLS/PDF; noticias del organismo.
  Nota: Verificado (último mes: septiembre 2026). Noticias: https://www.puertos.es/comunicacion. Sin RSS.
- **Salvamento Marítimo (SASEMAR)** — mar/ES · varias por semana · **sin verificar**
  https://www.salvamentomaritimo.es/
  Noticias de emergencias y rescates, balances de actividad, flota y medios.
  Nota: NO verificado: cadena de certificados TLS incompleta en el servidor (curl falla la validación) y robots bloquea WebFetch. Comprobar en navegador.
- **ERA – Agencia Ferroviaria de la Unión Europea – News** — tierra/UE · quincenal
  https://www.era.europa.eu/events-news/news_en
  Noticias sobre autorizaciones de vehículos, ERTMS, certificados de seguridad, interoperabilidad y registros.
  RSS/API: https://www.era.europa.eu/rss.xml
  Nota: RSS verificado. Última noticia 15/10/2026.
- **Comisiones de investigación de accidentes: CIAF (ferroviario), CIAIAC (aviación civil), CIAIM (marítimo)** — transversal/ES · según suceso; informes anuales
  https://www.transportes.gob.es/organos-colegiados/ciaf
  Informes finales, notas preliminares y recomendaciones de seguridad de accidentes ferroviarios, aéreos y marítimos.
  Nota: CIAF verificado (nota primeras 24 h accidente de Urda). CIAIAC: https://www.transportes.gob.es/organos-colegiados/ciaiac ; CIAIM: https://www.transportes.gob.es/organos-colegiados/ciaim (ambas 200). Los dominios antiguos ciaiac.es/ciaim.es redirigen o no resuelven.

## Operadores públicos (2)

- **Adif – Notas de prensa** — tierra/ES · diaria
  https://www.adif.es/comunicacion/notas-prensa
  Notas de prensa del administrador de infraestructuras: obras, licitaciones, cortes de línea, incidencias, nuevas estaciones.
  Nota: Verificado (nota 'Accidente en Urda (Toledo)' destacada). Sin RSS.
- **Renfe – Sala de prensa (Grupo Renfe)** — tierra/ES · diaria
  https://grupo.renfe.com/es/es/sala-de-prensa
  Notas de prensa del operador: servicios, resultados, licitaciones de material rodante, incidencias, Renfe Mercancías.
  Nota: Verificado por WebFetch ('Renfe al día'). Página muy dinámica (JS); sin RSS, ofrece avisos por WhatsApp.

## Estadística y datos (4)

- **INE – Estadística de Transporte de Viajeros (TV)** — tierra/ES · mensual (~día 12-15, datos t-2)
  https://www.ine.es/dyngs/INEbase/es/operacion.htm?c=Estadistica_C&cid=1254736176906&menu=ultiDatos&idp=1254735576820
  Viajeros mensuales en transporte urbano, interurbano (autobús, ferrocarril, aéreo, marítimo) y especial/discrecional.
  RSS/API: https://servicios.ine.es/wstempus/js/ES/OPERACIONES_DISPONIBLES
  Nota: Verificado: último dato agosto 2026 (371,6 millones de viajeros, +3,3 %). API JSON Tempus3 verificada (listado de operaciones); series TV accesibles por código de tabla.
- **Observatorio de la Movilidad Metropolitana (OMM)** — tierra/ES · anual (informe 2026 con datos 2024)
  https://observatoriomovilidad.es/
  Informe anual de movilidad metropolitana (oferta, demanda, financiación de autoridades de transporte), monografías y plataforma SIOMM.
  Nota: Verificado por WebFetch. Sin RSS.
- **Eurostat – Estadísticas de transporte** — transversal/UE · mensual/trimestral/anual según dataset
  https://ec.europa.eu/eurostat/web/transport/overview
  Series de pasajeros y mercancías por modo, flota, seguridad vial, aeropuertos y puertos; comparativas España/UE.
  RSS/API: https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/tran_r_avpa_nm
  Nota: API JSON-stat verificada (dataset tran_r_avpa_nm). Sustituir el código de dataset según necesidad (avia_paoc, rail_pa_quartal, mar_mp_aa_cph…).
- **OTLE – Observatorio del Transporte y la Logística en España** — transversal/ES · anual + actualizaciones mensuales/trimestrales de datos
  https://otle.transportes.gob.es/
  Informe anual (XIII ed. 2025-2026), monográficos (p. ej. planes de movilidad al trabajo, jul. 2026), indicadores y datos abiertos de movilidad y logística.
  Nota: Verificado (redirección desde observatoriotransporte.mitma.es). Sin RSS; formulario de suscripción a novedades. Estadística ministerial general: https://www.transportes.gob.es/informacion-para-el-ciudadano/informacion-estadistica

## Jurisprudencia (2)

- **CENDOJ – Buscador de jurisprudencia del CGPJ (Tribunal Supremo, AN, TSJ)** — transversal/ES · continua
  https://www.poderjudicial.es/search/indexAN.jsp
  Sentencias sobre concesiones, contratación pública de transporte, responsabilidad, derechos de pasajeros, tasas y cánones.
  Nota: Verificado. Aviso legal: solo consulta personal; prohibida la descarga masiva. Búsqueda por ECLI/ROJ, órgano y legislación citada.
- **TJUE – Tribunal de Justicia de la UE – Comunicados de prensa** — transversal/UE · varias por semana
  https://curia.europa.eu/site/jcms/d2_5158/en/
  Comunicados de sentencias y conclusiones (derechos de pasajeros Reg. 261/2004 y 1371/2007, ayudas de Estado, contratación, cabotaje).
  Nota: Verificado (comunicados 48/2026 y 49/2026). La URL antigua /jcms/jcms/Jo2_7052/ redirige aquí (la variante /es/ devolvió 403 a curl). Sin RSS localizado; jurisprudencia completa en https://curia.europa.eu/juris/

## Asociaciones sectoriales (12)

- **A4E – Airlines for Europe – News** — aire/UE · quincenal
  https://www.a4e.eu/news
  Posicionamientos de las grandes aerolíneas europeas: EES/Schengen, ATC, tasas, SAF, derechos de pasajeros.
  Nota: Verificado (12/10/2026). Sin RSS.
- **ACI EUROPE – Airports Council International Europe – Press releases** — aire/UE · semanal; tráfico mensual
  https://www.aci-europe.org/media-room/press-releases.html
  Informes mensuales de tráfico aeroportuario europeo, posicionamientos sobre tasas, capacidad y sostenibilidad.
  Nota: Verificado (22/10/2026). Sin RSS.
- **ALA – Asociación de Líneas Aéreas – Comunicación** — aire/ES · varias al mes
  https://www.alaspain.com/comunicacion/
  Notas de prensa y balances de tráfico aéreo en España, posicionamientos sobre tasas de Aena, conectividad insular, SAF.
  Nota: Portada verificada por WebFetch (dominio actual alaspain.com; alaspain.es no resuelve). Sin RSS.
- **ANAVE – Asociación de Navieros Españoles** — mar/ES · mensual (boletín) + notas
  https://anave.es/prensa/
  Notas de prensa, boletín informativo mensual, informe anual de la marina mercante y el transporte marítimo español.
  RSS/API: https://anave.es/feed/
  Nota: RSS verificado (WordPress). Página de prensa confirmada.
- **Interferry – News releases** — mar/internacional · mensual
  https://interferry.com/news-releases/
  Noticias de la industria del ferry: seguridad, regulación OMI, descarbonización, conferencia anual.
  RSS/API: https://interferry.com/feed/
  Nota: RSS verificado. Última nota 07/05/2026 (baja frecuencia).
- **ANETRA – Asociación Nacional de Empresarios de Transportes en Autocares (ANETRA Informa)** — tierra/ES · varias por semana
  https://anetra-informa.es/noticias
  Noticias del autocar discrecional y turístico: normativa, tacógrafo, ayudas, jornadas, circulares para asociados.
  RSS/API: https://anetra-informa.es/feed/
  Nota: RSS verificado (WordPress). Última noticia 30/10/2026 (traslado de sede). Web corporativa: https://anetra.es/
- **ATUC – Asociación de Empresas Gestoras de los Transportes Urbanos Colectivos** — tierra/ES · semanal · **sin verificar**
  https://www.atuc.es/
  Noticias y posicionamientos de operadores urbanos (financiación del transporte público, tarifas, descarbonización de flotas).
  Nota: NO verificado: cadena TLS incompleta en el servidor (curl) y robots bloquea WebFetch. Comprobar en navegador.
- **CONFEBUS – Confederación Española de Transporte en Autobús** — tierra/ES · varias por semana
  https://confebus.org/publicaciones/categoria/1/noticias
  Posicionamientos sectoriales, notas de prensa, revista CONFEBUS, informes y jornadas del transporte en autobús.
  Nota: Verificado (03/11/2026: comunicado accidente ferroviario de Toledo; adhesión a IRU por precio del combustible). Sin RSS; newsletter 'CONFEBUS News'.
- **FENEBÚS – Federación Nacional Empresarial de Transporte en Autobús** — tierra/ES · irregular · **sin verificar**
  https://www.fenebus.es/
  Notas de prensa y posicionamientos de la federación de autobuses (interurbano y discrecional).
  Nota: NO verificado / ALERTA: el 04/11/2026 el dominio redirige a un sitio ajeno y su /feed/ sirve una 'revista literaria' (dominio comprometido o caducado). No enlazar hasta confirmar nuevo dominio oficial.
- **Fundación de los Ferrocarriles Españoles (FFE) – Noticias** — tierra/ES · semanal
  https://www.ffe.es/noticias/
  Noticias institucionales, jornadas, estudios, Museo del Ferrocarril y publicaciones ferroviarias.
  Nota: Verificado (28/10/2026: comunicado por accidente ferroviario). Sin RSS; boletín por correo.
- **IRU – International Road Transport Union – Newsroom** — tierra/internacional · varias por semana
  https://www.iru.org/news-resources/newsroom
  Noticias de transporte por carretera (autobús/autocar y mercancías): normativa UE, conductores, combustible, digitalización.
  RSS/API: https://www.iru.org/rss.xml
  Nota: RSS verificado. Última noticia 29/10/2026 sobre la norma digital de transporte en España.
- **UITP – Unión Internacional de Transporte Público – News** — tierra/internacional · varias por semana
  https://www.uitp.org/news/
  Posicionamientos sobre política europea de transporte público, informes, premios y eventos.
  Nota: Verificado (30/10/2026). /feed/ redirige a la portada: sin RSS; newsletter.

## Think tanks y academia (3)

- **Fundación Corell** — transversal/ES · semanal
  https://fundacioncorell.es/
  Artículos de think tank, Observatorio de la Transición Energética en el Transporte (OTEM), índices de mercancías e informes sectoriales.
  RSS/API: https://fundacioncorell.es/feed/
  Nota: RSS verificado (WordPress). Último artículo 28/10/2026.
- **ITF – International Transport Forum (OCDE)** — transversal/internacional · mensual
  https://www.itf-oecd.org/news
  Informes (ITF Transport Outlook), estadísticas comparadas, cumbre anual de ministros de transporte, estudios de política.
  Nota: Verificado por WebFetch pero la página de noticias muestra últimas entradas de mayo 2025 (posible migración a oecd.org). El sitio devuelve 403 a clientes no navegador.
- **Transport & Environment (T&E)** — transversal/UE · varias por semana
  https://www.transportenvironment.org/articles
  Análisis y campañas sobre descarbonización del transporte: CO2 de vehículos, aviación, marítimo, presupuesto UE.
  Nota: Verificado por WebFetch (lista de artículos sin fechas). El sitio devuelve 403 a clientes no navegador; /feed/ no verificable. Posible sección España: /es/

## Prensa especializada (16)

- **Aviación Digital** — aire/ES · diaria
  https://aviaciondigital.com/
  Noticias de aerolíneas, aeropuertos, rutas y regulación aérea en España y Latinoamérica.
  RSS/API: https://aviaciondigital.com/feed/
  Nota: RSS verificado. Última noticia 02/11/2026.
- **FlightGlobal** — aire/internacional · diaria
  https://www.flightglobal.com/
  Noticias de aviación comercial, fabricantes, aerolíneas, seguridad y regulación.
  RSS/API: https://www.flightglobal.com/feed/
  Nota: RSS verificado. Portada abierta; artículos con límite/registro y suscripción.
- **Fly News** — aire/ES · diaria
  https://fly-news.es/
  Noticias de aviación comercial, industria aeroespacial, aeropuertos y defensa en español.
  RSS/API: https://fly-news.es/feed/
  Nota: RSS verificado (WordPress).
- **Diario del Puerto** — mar/ES · diaria
  https://www.diariodelpuerto.com/
  Diario de logística, puertos, transporte marítimo y cadena de suministro en España.
  Nota: Verificado. Portada abierta; contenidos 'Plus' por suscripción. Sin RSS localizado.
- **Lloyd's List** — mar/internacional · diaria
  https://www.lloydslist.com/
  Titulares y análisis de shipping: mercados de contenedores, tanqueros, construcción naval, regulación OMI.
  Nota: Verificado por WebFetch (titulares visibles). Sitio devuelve 403 a clientes no navegador; sin RSS verificable. Artículos completos: suscripción.
- **Autobuses & Autocares** — tierra/ES · diaria
  https://www.autobusesyautocares.com/
  Noticias del sector del autobús y autocar: operadores, fabricantes, contratación pública, presupuestos EMT.
  RSS/API: https://www.autobusesyautocares.com/feed/all
  Nota: RSS verificado (actualizado 03/11/2026).
- **Carrilbus** — tierra/ES · diaria
  https://carrilbus.com/
  Noticias diarias de movilidad y transporte público de viajeros (autobús, concesiones, flotas, asociaciones).
  RSS/API: https://carrilbus.com/feed
  Nota: RSS verificado (WordPress). Última noticia 30/10/2026.
- **Intelligent Transport** — tierra/internacional · diaria
  https://www.intelligenttransport.com/
  Noticias y análisis de transporte público, MaaS, ticketing, autobús eléctrico y datos (serie 'Bright Horizons').
  Nota: Verificado por WebFetch. A clientes no navegador responde 405 y redirige a globalrailwayreview.com (misma editorial, Russell Publishing); feed no verificable.
- **International Railway Journal (IRJ)** — tierra/internacional · diaria
  https://www.railjournal.com/
  Noticias ferroviarias internacionales, licitaciones, material rodante y financiación.
  Nota: Verificado por WebFetch; el sitio devuelve 403 a clientes no navegador (feed no verificable). Newsletter 'IRJ Rail Brief'.
- **Nexotrans** — tierra/ES · diaria
  https://nexotrans.com/
  Noticias de transporte por carretera (mercancías y viajeros), logística, asociaciones y normativa.
  RSS/API: https://nexotrans.com/feed/
  Nota: RSS verificado (/rss redirige a /feed/). Última noticia 03/11/2026.
- **Railin (antes Trenvista)** — tierra/ES · diaria
  https://www.railin.net/es/
  Revista independiente del sector ferroviario: noticias, reportajes, podcast, mapa de la RFIG.
  RSS/API: https://www.railin.net/es/feed/
  Nota: trenvista.net redirige a railin.net (rebranding; logo 'Railin-antes-Trenvista'). RSS verificado. Últimas noticias 30/10/2026.
- **Railway Gazette International** — tierra/internacional · diaria
  https://www.railwaygazette.com/
  Noticias ferroviarias internacionales: contratos, material rodante, política UE, alta velocidad, mercancías.
  RSS/API: https://www.railwaygazette.com/news/feed/
  Nota: RSS verificado. Portada abierta; parte del contenido y datos requieren suscripción/registro.
- **Transporte Profesional** — tierra/ES · diaria
  https://transporteprofesional.es/
  Noticias de transporte por carretera, vehículo industrial, movilidad eléctrica y normativa.
  Nota: Verificado (02/11/2026). El enlace RSS del pie es un placeholder '#'; /feed/ y /rss → 404.
- **Vía Libre (Fundación de los Ferrocarriles Españoles)** — tierra/ES · diaria
  https://www.vialibre-ffe.com/noticias.asp
  Noticias ferroviarias diarias (Adif, Renfe, operadores privados, industria, internacional) y revista mensual.
  Nota: Verificado (04/11/2026: dimisión del ministro Óscar Puente). Sin RSS localizado (/rss, /feed → 404).
- **El Mercantil (sucesor de El Vigía)** — transversal/ES · diaria
  https://elmercantil.com/
  Diario de logística, transporte y puertos (equipo fundado por antiguos redactores de El Vigía).
  RSS/API: https://elmercantil.com/feed/
  Nota: RSS verificado. Última noticia 03/11/2026. ATENCIÓN: elvigia.com ya no aloja el diario logístico ('El Vigía de la Comunicación', contenido político/general) — no usar.
- **Hosteltur – Transportes** — transversal/ES · diaria (varias al día)
  https://www.hosteltur.com/transportes
  Noticias de transporte turístico: aerolíneas, Aena, Renfe, cruceros, autocares; muy rápida en actualidad política.
  RSS/API: https://www.hosteltur.com/rss/transportes
  Nota: RSS de sección verificado (application/xml). 03/11/2026 22:18: dimisión de Óscar Puente por el accidente de Urda.

## Cambios detectados respecto a la lista inicial del proyecto

- 2026-11-04 · Trenvista ya no publica en trenvista.net: su actividad continúa en railin.net.
- 2026-11-04 · fenebus.es presenta señales de sitio comprometido; no se usa como fuente hasta que se normalice.
- 2026-11-04 · El Vigía (elvigia.com) ha sido sustituido por elmercantil.com.
- 2026-11-04 · Flightglobal, Railway Gazette, Rail Business UK y Air Cargo News pertenecen desde el 31-12-2025 a ProMedia Group, no a DVV Media International.
- 2026-11-04 · La Asociación de Líneas Aéreas usa el dominio alaspain.com.
- 2026-11-04 · eurotransportmagazine.com redirige a un sitio ajeno: descartado.
- 2026-11-04 · anetra-informa.es/noticias (indicada en el proyecto) queda incorporada como fuente de prensa sectorial del autobús.
- 2026-11-06 · El Boletín Oficial de Cantabria y la web del Gobierno de Cantabria no admiten lectura automática; el Decreto 77/2026 se leyó en la reproducción de Noticias Jurídicas.
- 2026-11-05 · La nota de prensa de Wizz Air y la web de COPE no fueron accesibles; Facua y Diario del Puerto solo legibles en titular y entradilla.
