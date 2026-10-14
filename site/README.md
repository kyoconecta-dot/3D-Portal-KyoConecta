# Página do kit — kyoconecta.com.br/3dportal

Copie a pasta `3dportal/` (index.html + logo + favicon) para a raiz do site, de modo que fique em `https://kyoconecta.com.br/3dportal/`.

Bloqueio de indexação:
- já vai na página: `<meta name="robots" content="noindex, nofollow, noarchive">`;
- Cloudflare Pages: copie também `_headers` para a raiz do site (envia `X-Robots-Tag` em `/3dportal/*`);
- não coloque `/3dportal` no `robots.txt` com Disallow: isso impediria o Google de ler o noindex.

Logo e favicon: arquivos oficiais do design system KYŌ (`kyo-logo-horizontal-negativo.svg`, `kyo-favicon.png`).
