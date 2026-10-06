---
name: vale-documentos
description: Cria documentos HTML no estilo visual da Vale (tema escuro, paleta vinho/dourado/teal), para os trabalhos e entregas da disciplina DECC0294.
---

# Skill: Documentos no estilo Vale

## Quando usar

Use esta skill sempre que o usuário pedir para criar página HTML, relatório
visual, painel ou qualquer documento que deva seguir a identidade visual da
Vale usada neste projeto.

## Paleta obrigatória (copiar de vale-rh-3d.html)

```css
:root{
  --vinho:#8D0333; --dourado:#D4B277; --teal:#0AB0AB; --amarelo:#FEC84D;
  --fundo:#14161a; --caixa:#1c1f26; --caixa2:#242832; --linha:#333846;
  --txt:#eceff4; --txt2:#9aa3b2;
}
```

## Regras de estilo

1. Fundo escuro (`--fundo`), texto claro (`--txt`), texto secundário `--txt2`.
2. Tipografia: `"Segoe UI", Calibri, "Helvetica Neue", Arial, sans-serif`.
3. Título principal (h1) em `--dourado`; subtítulos de seção (h2) em `--teal`,
   caixa alta, letter-spacing, com borda inferior em `--linha`.
4. Caixas/painéis com `--caixa`, bordas `--linha`, raio de 4px.
5. Botões e chips: fundo `--caixa2`, destaque ativo em `--teal` ou `--vinho`.
6. Números importantes (KPIs) em `--dourado`, rótulos em caixa alta pequena.
7. Alertas/avisos em `--amarelo` com borda esquerda de 3px.
8. Sem dependências externas: HTML + CSS + JS em um único arquivo, sem CDN.

## Estrutura mínima do documento

```html
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Título do documento</title>
<style>/* paleta e estilos acima */</style>
</head>
<body>
<h1>Título</h1>
<p class="sub">Descrição curta</p>
<h2>Seção</h2>
<!-- conteúdo -->
</body>
</html>
```

## Checklist antes de entregar

- [ ] Paleta idêntica à de vale-rh-3d.html
- [ ] Contraste legível (fundo escuro, texto claro)
- [ ] Abre corretamente no navegador sem internet
- [ ] Referências e números com fonte declarada no próprio texto
