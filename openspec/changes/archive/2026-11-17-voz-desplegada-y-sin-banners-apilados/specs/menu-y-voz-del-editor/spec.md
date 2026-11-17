### Requisito: página de «La voz del editor» (cambio `voz-desplegada-y-sin-banners-apilados`, 17-11-2026)
En `/la-voz-del-editor/` la última columna se lee entera (marca, tema, fecha, titular, subtítulo, firma, foto con crédito y texto tal cual se publicó) y a la derecha, en una columna estrecha que no compite con ella, se enumeran las anteriores con fecha, tema y titular. En el móvil las anteriores van debajo.

#### Escenario: abrir la página con varias columnas
- DADO que hay tres columnas publicadas
- CUANDO un lector abre `/la-voz-del-editor/`
- ENTONCES ve completa la más reciente y, a la derecha, las otras dos enlazadas, de la más reciente a la más antigua

#### Escenario: el texto no se puede leer
- DADO que la página de la última columna no responde
- CUANDO se pinta la sección
- ENTONCES se ve su resumen con «Leer la columna completa» y el resto de la página igual
