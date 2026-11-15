# Borrador · Textos legales del formulario «Pide más información» de los banners

Estado: **borrador para que lo apruebe el editor jefe** (16-11-2026, cambio `banner-premium`). Mientras no lo apruebe, el formulario está apagado (`verticals/movilidad.json → publicidad.formulario.activo: false`) y el botón «Pide más información» se pinta como «Ir a la web». Conviene que lo revise también quien lleve la protección de datos de Avionline S.L.

## Planteamiento
- **Quién es responsable de qué.** El anunciante es el responsable del tratamiento de los datos que recibe para contestar. Avionline S.L. (titular de MOTICIAS) los recoge y los entrega por cuenta del anunciante y guarda una copia para acreditar el envío y el consentimiento: actúa como **encargado del tratamiento** del anunciante, con un contrato de encargo (art. 28 RGPD) que se firma con cada anunciante que active el formulario.
- **Base jurídica.** Consentimiento del interesado (art. 6.1.a RGPD), con casilla sin marcar.
- **Datos.** Solo los del formulario. Obligatorios: nombre, correo, código postal y país. El resto, opcional.
- **Conservación.** 12 meses desde el envío; después se vacían los campos personales (queda la fila sin datos, para las cifras).
- **Derechos.** Acceso, rectificación, supresión, oposición, limitación y portabilidad: ante el anunciante, o ante MOTICIAS, que los traslada; y reclamación ante la Agencia Española de Protección de Datos.
- **Sin otros usos.** MOTICIAS no usa estos datos para nada más ni los cede a terceros distintos del anunciante.

## Texto que ve el lector (bajo el formulario)
> **Quién recibe tus datos.** Los recibe {anunciante}, el anunciante, para contestarte; es el responsable de lo que haga con ellos y te informa en su política de privacidad. MOTICIAS (Avionline S.L.) solo los recoge y se los entrega por su cuenta, y guarda una copia durante 12 meses para demostrar el envío y tu consentimiento; no los usa para nada más ni los cede a nadie. Puedes ejercer tus derechos de acceso, rectificación, supresión, oposición, limitación y portabilidad ante el anunciante o escribiendo a MOTICIAS, y reclamar ante la Agencia Española de Protección de Datos. Más información en la [política de privacidad](https://www.moticias.com/privacidad/).

## Casilla (sin marcar)
> Acepto que MOTICIAS entregue estos datos a {anunciante} para que me contacte sobre este anuncio.

## Para encenderlo
1. El editor jefe aprueba estos textos (y, si quiere, los ajusta).
2. Se añade a `docs/legal/privacidad.md` un apartado «Formularios de los anuncios» y se republica la página de privacidad.
3. Con cada anunciante que use el formulario: contrato de encargo del tratamiento y una persona de contacto con correo en su cuenta del CRM (el gestor manda ahí los envíos; si no hay, llegan al editor jefe para que los reenvíe).
4. `publicidad.formulario.activo: true` en el vertical.
