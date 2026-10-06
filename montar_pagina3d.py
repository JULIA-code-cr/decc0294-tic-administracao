#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 MONTAGEM DA PAGINA 3D - QUADRO DE PESSOAL VALE (DADOS FICTICIOS)
 DECC0294 - Tecnologia da Informacao e Comunicacao Aplicada a Administracao
 UFMA - Curso de Administracao - 2026.2
=============================================================================

O QUE ESTE ARQUIVO FAZ
    Le vale_funcionarios.csv e escreve vale-rh-3d.html: uma pagina que desenha
    cada pessoa como uma esfera em 3D, com Three.js.

    Os dados vao embutidos no HTML de proposito. Assim a pagina abre com dois
    cliques, sem servidor e sem bloqueio de seguranca do navegador. Com os
    dados num CSV externo, o Chrome e o Firefox recusariam a leitura por
    seguranca de origem (CORS) assim que a pagina fosse aberta do disco.

COMO USAR

    python montar_pagina3d.py
        Le vale_funcionarios.csv, na mesma pasta, e escreve vale-rh-3d.html

    python montar_pagina3d.py decc0294-tic-administracao/dados/vale_funcionarios.csv
        Escolhe o caminho do CSV

BIBLIOTECA
    Three.js r147 em lib/three.min.js, na versao UMD. UMD e nao ESM porque o
    navegador bloqueia modulo em arquivo://; UMD abre em qualquer lugar. A
    pagina funciona sem internet: nada e buscado de CDN.

O QUE A PAGINA DEIXA DE FORA
    CPF, data de nascimento e email. Sao dado pessoal (LGPD), o arquivo sai da
    area de RH e nenhuma pergunta da analise depende deles.
=============================================================================
"""

import csv
import json
import os
import sys

CSV_PADRAO = "vale_funcionarios.csv"
SAIDA_PADRAO = "vale-rh-3d.html"
MODULO_GERADOR = os.path.join("decc0294-tic-administracao", "simulacao_rh_vale.py")

# coluna do csv -> chave curta usada no JavaScript
MAPA = [
    ("matricula", "m"), ("nome", "nome"), ("sexo", "sexo"),
    ("unidade", "unidade"), ("uf", "uf"), ("area", "area"),
    ("departamento", "depto"), ("cargo", "cargo"), ("nivel", "nivel"),
    ("idade", "idade"), ("data_admissao", "admissao"),
    ("tempo_empresa_anos", "tempo"), ("tipo_contrato", "contrato"),
    ("status", "status"), ("jornada_horas_semanais", "jornada"),
    ("horas_extras_mes", "he"), ("salario_base", "salario"),
    ("bonus_percentual", "bonus"), ("plano_saude", "plano"),
    ("vale_transporte", "vt"), ("vale_alimentacao", "va"),
    ("ultima_avaliacao", "nota"), ("desempenho", "desempenho"),
    ("potencial", "potencial"), ("risco_de_saida", "risco"),
    ("escolaridade", "escolaridade"), ("curso_ultimo", "curso"),
    ("gestor", "gestor"),
]
NUMERICOS = {"idade": int, "tempo": float, "salario": float, "bonus": int,
             "nota": int, "he": float, "jornada": int}

TEMPLATE = r"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Quadro de pessoal em 3D - base ficticia</title>
<style>
:root{
  --vinho:#8D0333; --dourado:#D4B277; --teal:#0AB0AB; --amarelo:#FEC84D;
  --fundo:#14161a; --caixa:#1c1f26; --caixa2:#242832; --linha:#333846;
  --txt:#eceff4; --txt2:#9aa3b2;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:var(--fundo);color:var(--txt);overflow:hidden;
  font:14px "Segoe UI",Calibri,"Helvetica Neue",Arial,sans-serif}
#cena{position:fixed;inset:0}
#cena canvas{display:block}

.painel{position:fixed;top:0;bottom:0;background:var(--caixa);z-index:5;
  overflow-y:auto;padding:14px 14px 46px;transition:transform .18s ease}
#esq{left:0;width:320px;border-right:1px solid var(--linha)}
#dir{right:0;width:326px;border-left:1px solid var(--linha)}
#esq.oculto{transform:translateX(-320px)}
#dir.oculto{transform:translateX(326px)}
.abrir{position:fixed;top:12px;z-index:6;background:var(--vinho);color:#fff;border:0;
  padding:8px 12px;border-radius:4px;cursor:pointer;font:13px inherit}
#abEsq{left:12px}
#abDir{right:12px}

h1{font-size:17px;color:var(--dourado);line-height:1.25}
.sub{color:var(--txt2);font-size:12px;margin:4px 0 6px;line-height:1.45}
h2{font-size:11px;letter-spacing:1.4px;color:var(--teal);text-transform:uppercase;
  margin:18px 0 8px;border-bottom:1px solid var(--linha);padding-bottom:5px}
.campo{display:block;font-size:11px;letter-spacing:.6px;color:var(--txt2);
  text-transform:uppercase;margin:11px 0 4px}
select,input{width:100%;background:var(--caixa2);color:var(--txt);
  border:1px solid var(--linha);border-radius:4px;padding:7px 8px;
  font:13px inherit}
select:focus,input:focus{outline:2px solid var(--teal);outline-offset:-1px}

.chips{display:flex;flex-wrap:wrap;gap:5px}
.chip{background:var(--caixa2);border:1px solid var(--linha);color:var(--txt2);
  border-radius:12px;padding:4px 9px;font-size:12px;cursor:pointer;user-select:none}
.chip[aria-pressed=false]{background:var(--vinho);border-color:var(--vinho);color:#fff}
.chip .n{opacity:.7;margin-left:4px}
.btns{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}
button.acao{flex:1 1 auto;background:var(--caixa2);color:var(--txt);
  border:1px solid var(--linha);border-radius:4px;padding:7px 9px;cursor:pointer;
  font:12px inherit}
button.acao:hover{border-color:var(--teal);color:var(--teal)}
button.acao[aria-pressed=true]{background:var(--teal);border-color:var(--teal);color:#06201f}

.kpis{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.kpi{background:var(--caixa2);border:1px solid var(--linha);border-radius:4px;padding:9px 10px}
.kpi .v{font-size:18px;font-weight:700;color:var(--dourado);line-height:1.15}
.kpi .r{font-size:10.5px;color:var(--txt2);text-transform:uppercase;
  letter-spacing:.5px;margin-top:2px}

#legenda{display:flex;flex-direction:column;gap:5px}
.item{display:flex;align-items:center;gap:8px;font-size:12.5px;color:var(--txt2)}
.item .bolinha{width:12px;height:12px;border-radius:50%;flex:0 0 12px;box-shadow:0 0 0 1px #0006}
.item .txt{flex:1 1 auto}
.item .ct{color:var(--txt);font-variant-numeric:tabular-nums}
.item.zerada{opacity:.35}

dl{display:grid;grid-template-columns:86px 1fr;gap:3px 8px;font-size:12.5px}
dt{color:var(--txt2)}
dd{color:var(--txt);overflow-wrap:anywhere}
#ficha h3{font-size:16px;color:var(--amarelo);line-height:1.2}
#ficha .mat{font-size:11.5px;color:var(--txt2);margin:2px 0 9px}
.vazio{color:var(--txt2);font-size:13px;line-height:1.5}
.alerta{color:var(--amarelo);font-size:12px;line-height:1.45;background:#FEC84D14;
  border-left:3px solid var(--amarelo);padding:8px 10px;border-radius:3px;margin-top:14px}
#qualidade div{font-size:12.5px;color:var(--txt2);line-height:1.5;margin-bottom:7px}
#qualidade b{color:var(--txt)}

#dica{position:fixed;pointer-events:none;z-index:9;background:#0d0f13f0;
  border:1px solid var(--teal);border-radius:4px;padding:7px 9px;font-size:12.5px;
  display:none;max-width:250px;box-shadow:0 6px 20px #0009}
#dica b{color:var(--amarelo)}
#rodape{position:fixed;left:332px;right:338px;bottom:8px;text-align:center;
  color:var(--txt2);font-size:11.5px;z-index:4;pointer-events:none;line-height:1.5}
#erro{display:none;position:fixed;inset:0;background:var(--fundo);z-index:20;padding:40px}
#erro code{background:#ffffff14;padding:2px 6px;border-radius:3px;color:var(--amarelo)}
@media (max-width:1080px){
  #rodape{left:12px;right:12px}
  .painel{width:290px}
  #esq.oculto{transform:translateX(-290px)}
  #dir.oculto{transform:translateX(290px)}
}
</style>
</head>
<body>

<div id="cena"></div>
<button class="abrir" id="abEsq" type="button">Filtros</button>
<button class="abrir" id="abDir" type="button">Numeros</button>

<aside class="painel" id="esq">
  <h1>Quadro de pessoal em 3D</h1>
  <p class="sub">Base ficticia de __N__ pessoas, gerada por script. Nao sao dados da Vale
  nem de pessoas reais.</p>

  <h2>Organizar no espaco</h2>
  <label class="campo" for="layout">Layout</label>
  <select id="layout">
    <option value="carreira">Escada de nivel x salario x area</option>
    <option value="desempenho">Avaliacao x nivel x tempo de casa</option>
    <option value="areas">Um bloco por area, altura pela idade</option>
  </select>
  <label class="campo" for="cor">Cor por</label>
  <select id="cor">
    <option value="nota">Avaliacao de desempenho (1 a 5)</option>
    <option value="risco">Risco de saida</option>
    <option value="sexo">Sexo</option>
    <option value="area">Area de negocio</option>
    <option value="contrato">Tipo de contrato</option>
  </select>
  <label class="campo" for="tamanho">Tamanho da esfera</label>
  <select id="tamanho">
    <option value="fixo">Igual para todos</option>
    <option value="salario">Proporcional ao salario</option>
    <option value="tempo">Proporcional ao tempo de casa</option>
  </select>

  <h2>Filtros</h2>
  <label class="campo">Nivel (clique para ligar e desligar)</label>
  <div class="chips" id="fNivel"></div>
  <label class="campo" for="fArea">Area</label>
  <select id="fArea"></select>
  <label class="campo" for="fContrato">Tipo de contrato</label>
  <select id="fContrato"></select>
  <label class="campo" for="fStatus">Situacao</label>
  <select id="fStatus"></select>
  <label class="campo" for="fSexo">Sexo</label>
  <select id="fSexo"></select>
  <label class="campo" for="busca">Buscar por nome ou matricula</label>
  <input type="search" id="busca" list="listaNomes" placeholder="ex.: Ana, VAL-0042" autocomplete="off">
  <datalist id="listaNomes"></datalist>

  <div class="btns">
    <button class="acao" id="limpar" type="button">Limpar filtros</button>
    <button class="acao" id="girar" type="button" aria-pressed="false">Girar sozinho</button>
    <button class="acao" id="recuar" type="button">Recentralizar</button>
  </div>

  <h2>Legenda</h2>
  <div id="legenda"></div>
</aside>

<aside class="painel" id="dir">
  <h2>Numeros do que esta na tela</h2>
  <div class="kpis" id="kpis" aria-live="polite"></div>
  <h2>Qualidade do dado no recorte</h2>
  <div id="qualidade"></div>
  <div id="ficha">
    <h2>Pessoa escolhida</h2>
    <p class="vazio" id="fichaVazia">Clique numa esfera para ver a ficha e as ligacoes
    de gestao. O fio dourado vai para o gestor, os fios turquesa para quem ela lidera.</p>
    <div id="fichaDados" hidden></div>
  </div>
  <p class="alerta">Esta pagina mostra so o dado necessario para a analise. CPF, data de
  nascimento e email ficaram de fora por serem dado pessoal (LGPD).</p>
</aside>

<div id="dica" role="status"></div>
<p id="rodape">Arraste para girar. Roda do mouse para aproximar. Clique numa esfera para
ver a ficha. Duplo clique limpa a selecao. Tecla R recentraliza.</p>
<div id="erro"><h1>A pagina nao conseguiu carregar</h1><p id="erroMsg"></p></div>

<script src="lib/three.min.js"></script>
<script src="lib/OrbitControls.js"></script>
<script>
(function () {
"use strict";

var PESSOAS = __DADOS__;
var FAIXAS = __FAIXAS__;
var N_TOTAL = PESSOAS.length;
var NIVEL_ORDEM = ["Operacional","Tecnico","Analista","Especialista",
                   "Coordenador","Gerencia","Diretoria"];

var CORES = {
  dourado: 0xD4B277, teal: 0x0AB0AB,
  nota: [0xc0392b, 0xe67e22, 0xf1c40f, 0x8bc34a, 0x1abc9c],
  risco: {"Baixo":0x1abc9c, "Medio":0xf1c40f, "Alto":0xe74c3c},
  sexo: {"F":0xFEC84D, "M":0x0AB0AB},
  contrato: {"CLT":0x0AB0AB, "Terceirizado":0x8D0333, "Estagio":0xFEC84D,
             "Contrato por prazo":0x7A8AA0}
};

var estado = {layout:"carreira", cor:"nota", tamanho:"fixo", niveis:{},
              area:"", contrato:"", status:"", sexo:"", busca:"", selecionada:null};

var cena, camera, render, controles, grupoPessoas, grupoLinhas, grupoEixos;
var geoEsfera, malhas = [], porMatricula = {};
var areaLista = [], areaIndice = {}, valores = {}, raio = new THREE.Raycaster();
var ponteiro = new THREE.Vector2(), sobDedo = null, ultimaCor = null;

function $(id) { return document.getElementById(id); }

function unicos(lista) {
  var out = [], visto = {};
  for (var i = 0; i < lista.length; i++) {
    if (!visto[lista[i]]) { visto[lista[i]] = 1; out.push(lista[i]); }
  }
  return out.sort();
}

function dinheiro(v) {
  return "R$ " + v.toLocaleString("pt-BR",
    {minimumFractionDigits:2, maximumFractionDigits:2});
}

function escala(valor, deMin, deMax, paraMin, paraMax) {
  if (deMax <= deMin) return (paraMin + paraMax) / 2;
  return paraMin + (valor - deMin) / (deMax - deMin) * (paraMax - paraMin);
}

function corHex(n) { return "#" + ("000000" + n.toString(16)).slice(-6); }

function corDeArea(nome) {
  var i = areaIndice[nome];
  return new THREE.Color("hsl(" +
    (i === undefined ? 0 : Math.round(i * 137.5) % 360) + ",62%,58%)").getHex();
}

function preparar() {
  valores = {};
  ["salario", "nota", "idade", "tempo"].forEach(function (c) {
    var lista = PESSOAS.map(function (p) { return p[c]; });
    valores[c] = {min: Math.min.apply(null, lista), max: Math.max.apply(null, lista)};
  });
  areaLista = unicos(PESSOAS.map(function (p) { return p.area; }));
  areaLista.forEach(function (a, i) { areaIndice[a] = i; });
  NIVEL_ORDEM.forEach(function (n) { estado.niveis[n] = true; });
}

function criarCena() {
  cena = new THREE.Scene();
  cena.background = new THREE.Color(0x14161a);
  cena.fog = new THREE.Fog(0x14161a, 340, 900);
  camera = new THREE.PerspectiveCamera(52, innerWidth / innerHeight, 0.5, 2600);
  camera.position.set(200, 165, 265);
  render = new THREE.WebGLRenderer({antialias: true});
  render.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  render.setSize(innerWidth, innerHeight);
  $("cena").appendChild(render.domElement);
  controles = new THREE.OrbitControls(camera, render.domElement);
  controles.enableDamping = true;
  controles.dampingFactor = 0.08;
  controles.maxPolarAngle = Math.PI * 0.49;
  controles.minDistance = 45;
  controles.maxDistance = 1000;
  controles.addEventListener("end", desenharNumeros);

  cena.add(new THREE.HemisphereLight(0x9fc4ff, 0x241c24, 0.8));
  var principal = new THREE.DirectionalLight(0xffffff, 0.62);
  principal.position.set(170, 280, 190);
  cena.add(principal);
  var piso = new THREE.Mesh(new THREE.CircleGeometry(330, 80),
    new THREE.MeshPhongMaterial({color: 0x1b1e25, shininess: 0}));
  piso.rotation.x = -Math.PI / 2;
  piso.position.y = -1;
  cena.add(piso);
  var grade = new THREE.GridHelper(620, 24, 0x3a4150, 0x262b35);
  grade.material.transparent = true;
  grade.material.opacity = 0.4;
  cena.add(grade);

  grupoPessoas = new THREE.Group();
  grupoLinhas = new THREE.Group();
  grupoEixos = new THREE.Group();
  cena.add(grupoPessoas, grupoLinhas, grupoEixos);
}

function criarEsferas() {
  geoEsfera = new THREE.SphereGeometry(5, 26, 18);
  PESSOAS.forEach(function (p, i) {
    p.indice = i;
    var malha = new THREE.Mesh(geoEsfera, new THREE.MeshPhongMaterial(
      {color: 0xcccccc, emissive: 0x000000, shininess: 55, specular: 0x404040,
       transparent: true, opacity: 1}));
    malha.userData = p;
    malha.position.set(0, 6, 0);
    grupoPessoas.add(malha);
    malhas.push(malha);
    porMatricula[p.m] = malha;
  });
}

function nivelY(p) {
  return 14 + Math.max(0, NIVEL_ORDEM.indexOf(p.nivel)) * 28;
}

function tamanhoDe(p) {
  if (estado.tamanho === "salario") return escala(p.salario,
    valores.salario.min, valores.salario.max, 0.62, 1.8);
  if (estado.tamanho === "tempo") return escala(p.tempo,
    valores.tempo.min, valores.tempo.max, 0.6, 1.6);
  return 1;
}

function posicaoDe(p) {
  var i, lin, col, base;
  if (estado.layout === "desempenho") {
    return new THREE.Vector3(
      escala(p.tempo, valores.tempo.min, valores.tempo.max, -110, 110),
      nivelY(p),
      escala(p.nota, 1, 5, -70, 70) +
        (areaIndice[p.area] - (areaLista.length - 1) / 2) * 5);
  }
  if (estado.layout === "areas") {
    base = (areaIndice[p.area] - (areaLista.length - 1) / 2) * 36;
    var iguais = PESSOAS.filter(function (q) { return q.area === p.area; });
    i = iguais.indexOf(p);
    col = i % 5;
    lin = Math.floor(i / 5) % 5;
    return new THREE.Vector3(
      base + (col - 2) * 13,
      escala(p.idade, valores.idade.min, valores.idade.max, 16, 200),
      (lin - 2) * 13);
  }
  return new THREE.Vector3(
    escala(p.nota, 1, 5, -72, 72),
    nivelY(p),
    escala(p.salario, valores.salario.min, valores.salario.max, -95, 95) +
      (areaIndice[p.area] - (areaLista.length - 1) / 2) * 4);
}

function corDe(p) {
  if (estado.cor === "risco") return CORES.risco[p.risco] || 0x9aa3b2;
  if (estado.cor === "sexo") return CORES.sexo[p.sexo] || 0x9aa3b2;
  if (estado.cor === "area") return corDeArea(p.area);
  if (estado.cor === "contrato") return CORES.contrato[p.contrato] || 0x9aa3b2;
  return CORES.nota[p.nota - 1] || 0x9aa3b2;
}

function casar(p) {
  if (!estado.niveis[p.nivel]) return false;
  if (estado.area && p.area !== estado.area) return false;
  if (estado.contrato && p.contrato !== estado.contrato) return false;
  if (estado.status && p.status !== estado.status) return false;
  if (estado.sexo && p.sexo !== estado.sexo) return false;
  if (estado.busca) {
    var alvo = (p.nome + " " + p.m).toLowerCase();
    if (alvo.indexOf(estado.busca) < 0) return false;
  }
  return true;
}

function porM(m) {
  return PESSOAS.filter(function (x) { return x.m === m; })[0] || null;
}

function relacoes(p) {
  var saida = [];
  if (p.gestor && porMatricula[p.gestor]) {
    saida.push({outro: porMatricula[p.gestor], cor: CORES.dourado, pessoa: p});
  }
  PESSOAS.forEach(function (q) {
    if (q.gestor === p.m) {
      saida.push({outro: porMatricula[q.m], cor: CORES.teal, pessoa: q});
    }
  });
  return saida;
}

function curva(a, b, cor, opacidade) {
  var meio = a.position.clone().add(b.position).multiplyScalar(0.5);
  meio.y += 14 + a.position.distanceTo(b.position) * 0.06;
  var caminho = new THREE.QuadraticBezierCurve3(
    a.position.clone(), meio, b.position.clone());
  var tubo = new THREE.Mesh(new THREE.TubeGeometry(caminho, 26, 0.5, 6, false),
    new THREE.MeshBasicMaterial({color: cor, transparent: true, opacity: opacidade}));
  grupoLinhas.add(tubo);
  var t = 0.55;
  var bola = new THREE.Mesh(new THREE.SphereGeometry(1.1, 10, 8),
    new THREE.MeshBasicMaterial({color: cor, transparent: true, opacity: opacidade}));
  bola.position.copy(caminho.getPoint(t));
  grupoLinhas.add(bola);
}

function atualizar() {
  malhas.forEach(function (m) {
    var p = m.userData;
    var dentro = casar(p);
    m.userData.dentro = dentro;
    var sel = estado.selecionada === p.m;
    var c = corDe(p);
    m.position.copy(posicaoDe(p));
    m.scale.setScalar(dentro ? tamanhoDe(p) : 0.5);
    m.material.color.setHex(c);
    m.material.emissive.setHex(sel ? c : 0x000000);
    m.material.emissiveIntensity = sel ? 0.8 : 0;
    m.material.opacity = dentro ? 1 : 0.09;
    m.material.depthWrite = dentro;
  });
  desenharLinhas();
  desenharNumeros();
  desenharKpis();
  desenharLegenda();
  desenharQualidade();
  atualizarChips();
}

function numerosVisiveis() {
  return malhas.filter(function (m) { return m.userData.dentro; });
}

function desenharNumeros() {
  while (grupoEixos.children.length) {
    var f = grupoEixos.children.pop();
    if (f.material.map) f.material.map.dispose();
    f.material.dispose();
  }
  var alcance = camera.position.distanceTo(controles.target);
  numerosVisiveis().forEach(function (m) {
    if (alcance > 330) return;
    if (m.position.distanceTo(controles.target) > 300) return;
    var cv = document.createElement("canvas");
    cv.width = 128; cv.height = 40;
    var ctx = cv.getContext("2d");
    ctx.fillStyle = "rgba(13,15,19,.72)";
    ctx.beginPath();
    if (ctx.roundRect) { ctx.roundRect(2, 2, 124, 36, 9); }
    else { ctx.rect(2, 2, 124, 36); }
    ctx.fill();
    ctx.font = "bold 22px Calibri, 'Segoe UI', sans-serif";
    ctx.fillStyle = estado.selecionada === m.userData.m ? "#FEC84D" : "#c8cedb";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(m.userData.m, 64, 20);
    var tex = new THREE.CanvasTexture(cv);
    tex.minFilter = THREE.LinearFilter;
    var sp = new THREE.Sprite(new THREE.SpriteMaterial(
      {map: tex, transparent: true, depthTest: false, depthWrite: false}));
    sp.scale.set(21, 6.6, 1);
    sp.position.copy(m.position).add(
      new THREE.Vector3(0, tamanhoDe(m.userData) * 5 + 8, 0));
    grupoEixos.add(sp);
  });
}

function mostrarDica(p, x, y) {
  var d = $("dica");
  d.innerHTML = "<b>" + p.nome + "</b><br>" + p.m + " &middot; " + p.cargo +
    "<br>" + p.nivel + " &middot; nota " + p.nota + " &middot; " + dinheiro(p.salario);
  d.style.display = "block";
  var l = Math.min(x + 16, innerWidth - 262);
  var a = Math.min(y + 16, innerHeight - 96);
  d.style.left = l + "px";
  d.style.top = a + "px";
}

function esconderDica() { $("dica").style.display = "none"; }

function aoMover(ev) {
  ponteiro.x = (ev.clientX / innerWidth) * 2 - 1;
  ponteiro.y = -(ev.clientY / innerHeight) * 2 + 1;
  raio.setFromCamera(ponteiro, camera);
  var acertos = raio.intersectObjects(grupoPessoas.children, false);
  var alvo = null;
  for (var i = 0; i < acertos.length; i++) {
    if (acertos[i].object.userData.dentro) { alvo = acertos[i].object; break; }
  }
  if (alvo) {
    mostrarDica(alvo.userData, ev.clientX, ev.clientY);
    render.domElement.style.cursor = "pointer";
  } else {
    esconderDica();
    render.domElement.style.cursor = "grab";
  }
}

function aoClicar(ev) {
  ponteiro.x = (ev.clientX / innerWidth) * 2 - 1;
  ponteiro.y = -(ev.clientY / innerHeight) * 2 + 1;
  raio.setFromCamera(ponteiro, camera);
  var acertos = raio.intersectObjects(grupoPessoas.children, false);
  for (var i = 0; i < acertos.length; i++) {
    if (acertos[i].object.userData.dentro) {
      estado.selecionada = acertos[i].object.userData.m;
      centralizar(acertos[i].object);
      atualizar();
      mostrarFicha(porM(estado.selecionada));
      return;
    }
  }
  estado.selecionada = null;
  atualizar();
  mostrarFicha(null);
}

function centralizar(malha) {
  var alvo = malha.position.clone();
  var dir = camera.position.clone().sub(controles.target).normalize();
  controles.target.copy(alvo);
  camera.position.copy(alvo.clone().add(dir.multiplyScalar(120)));
}

function desenharLinhas() {
  while (grupoLinhas.children.length) {
    var x = grupoLinhas.children.pop();
    x.geometry.dispose();
    if (x.material.dispose) x.material.dispose();
  }
  var alvo = estado.selecionada ? porM(estado.selecionada) : null;
  if (alvo) {
    var mAlvo = porMatricula[alvo.m];
    relacoes(alvo).forEach(function (r) {
      if (!r.outro) return;
      var op = r.outro.userData.dentro ? 0.95 : 0.3;
      curva(r.outro, mAlvo, r.cor, op);
    });
    return;
  }
  PESSOAS.forEach(function (q) {
    if (!q.gestor || !porMatricula[q.gestor]) return;
    if (!porMatricula[q.m].userData.dentro && !porMatricula[q.gestor].userData.dentro) return;
    curva(porMatricula[q.m], porMatricula[q.gestor], CORES.teal, 0.16);
  });
}

function linha(campo, valor) {
  return "<dt>" + campo + "</dt><dd>" + valor + "</dd>";
}

function mostrarFicha(p) {
  var vazio = $("fichaVazia");
  var dados = $("fichaDados");
  if (!p) {
    vazio.hidden = false;
    dados.hidden = true;
    dados.innerHTML = "";
    return;
  }
  vazio.hidden = true;
  dados.hidden = false;
  var gerente = p.gestor ? porM(p.gestor) : null;
  var liderados = PESSOAS.filter(function (q) { return q.gestor === p.m; });
  var html = "<h3>" + p.nome + "</h3><p class='mat'>" + p.m + " &middot; " +
    p.sexo + " &middot; " + p.idade + " anos</p><dl>";
  html += linha("Unidade", p.unidade + " (" + p.uf + ")");
  html += linha("Area", p.area);
  html += linha("Depto", p.depto);
  html += linha("Cargo", p.cargo);
  html += linha("Nivel", p.nivel);
  html += linha("Admissao", p.admissao + " (" + p.tempo.toFixed(1) + " anos)");
  html += linha("Contrato", p.contrato);
  html += linha("Jornada", p.jornada + " h/semana");
  html += linha("Horas extras", p.he.toFixed(1) + " h/mes");
  html += linha("Salario base", dinheiro(p.salario));
  html += linha("Bonus", p.bonus + "%");
  html += linha("Beneficios", [p.plano, p.vt, p.va].filter(function (v) {
    return v && v.toLowerCase() !== "nao";
  }).join(" &middot; ") || "nenhum beneficio");
  html += linha("Ultima nota", p.nota + " (" + p.desempenho + ")");
  html += linha("Potencial", p.potencial);
  html += linha("Risco de saida", p.risco);
  html += linha("Formacao", p.escolaridade + (p.curso ? " &middot; " + p.curso : ""));
  html += linha("Gestor", gerente ? gerente.nome + " (" + gerente.m + ")" : "sem gestor");
  html += linha("Lidera", liderados.length
    ? liderados.length + " pessoa(s): " + liderados.map(function (q) {
        return q.nome.split(" ")[0] + " (" + q.m + ")";
      }).join(", ")
    : "ninguem");
  html += "</dl>";
  dados.innerHTML = html;
}

function desenharKpis() {
  var vis = numerosVisiveis();
  var qtd = vis.length;
  var soma = 0, bons = 0, alto = 0, contratos = 0, genders = {F: 0, M: 0};
  vis.forEach(function (m) {
    var p = m.userData;
    soma += p.salario;
    if (p.nota >= 4) bons++;
    if (p.contrato !== "CLT") contratos++;
    if (p.risco === "Alto") alto++;
    if (genders[p.sexo] !== undefined) genders[p.sexo]++;
  });
  var n = qtd || 1;
  var cards = [
    ["Pessoas na tela", qtd, "de " + N_TOTAL + " na base"],
    ["Folha no recorte", dinheiro(soma), "soma dos salarios base"],
    ["Salario medio", dinheiro(soma / n), qtd ? "no recorte filtrado" : "sem gente"],
    ["Nota 4 ou 5", (bons / n * 100).toFixed(0) + "%", bons + " de " + qtd],
    ["Risco de saida alto", (alto / n * 100).toFixed(0) + "%", alto + " pessoas"],
    ["Nao CLT", (contratos / n * 100).toFixed(0) + "%", contratos + " pessoas"],
    ["Feminino / masculino", genders.F + " / " + genders.M, "composicao do recorte"]
  ];
  $("kpis").innerHTML = cards.map(function (c) {
    return "<div class='kpi'><div class='v'>" + c[1] +
      "</div><div class='r'>" + c[0] + "<br>" + c[2] + "</div></div>";
  }).join("");
}

function desenharQualidade() {
  var vis = numerosVisiveis();
  if (!vis.length) {
    $("qualidade").innerHTML = "<div><b>Nenhuma pessoa no recorte.</b> " +
      "Solte um filtro para voltar a ver a base.</div>";
    return;
  }
  var n = vis.length;
  var semAvaliacao = vis.filter(function (m) { return !m.userData.nota; }).length;
  var fora = vis.filter(function (m) {
    var p = m.userData;
    return p.salario > valores.salario.max * 0.92;
  }).length;
  var msg = [
    ["Base exibida", n + " de " + N_TOTAL + " pessoa(s) (" +
      (n / N_TOTAL * 100).toFixed(0) + "% do total)."],
    ["Amostra pequena", n < 12
      ? "Com menos de 12 pessoas, qualquer media fica instavel. Use para olhar caso, nao para concluir."
      : "Amostra grande o bastante para leitura de tendencia."],
    ["Avaliacao ausente", semAvaliacao
      ? semAvaliacao + " sem nota registrada."
      : "Todas com nota de avaliacao."],
    ["Salarios no topo", fora ? fora + " acima de 92% do maior salario da base." :
      "Nenhum salario no topo da faixa."],
    ["Dado ficticio", "Base gerada por script. Serve para treinar a leitura, nao para decidir sobre pessoas."]
  ];
  $("qualidade").innerHTML = msg.map(function (x) {
    return "<div><b>" + x[0] + ".</b> " + x[1] + "</div>";
  }).join("");
}

function desenharLegenda() {
  var vis = numerosVisiveis();
  var grupos = {};
  vis.forEach(function (m) {
    var p = m.userData;
    var chave, cor;
    if (estado.cor === "nota") { chave = "Nota " + p.nota; cor = CORES.nota[p.nota - 1]; }
    else if (estado.cor === "risco") { chave = "Risco " + p.risco; cor = CORES.risco[p.risco]; }
    else if (estado.cor === "sexo") { chave = p.sexo === "F" ? "Feminino" : "Masculino";
      cor = CORES.sexo[p.sexo]; }
    else if (estado.cor === "contrato") { chave = p.contrato; cor = CORES.contrato[p.contrato]; }
    else { chave = p.area; cor = corDeArea(p.area); }
    if (!grupos[chave]) grupos[chave] = {n: 0, cor: cor};
    grupos[chave].n++;
  });
  var html = Object.keys(grupos).sort().map(function (k) {
    return "<div class='item'><span class='bolinha' style='background:" +
      corHex(grupos[k].cor) + "'></span><span class='txt'>" + k +
      "</span><span class='ct'>" + grupos[k].n + "</span></div>";
  }).join("");
  $("legenda").innerHTML = html || "<p class='vazio'>Sem pessoas no recorte.</p>";
}

function atualizarChips() {
  var contagem = {};
  malhas.forEach(function (m) {
    if (m.userData.dentro) contagem[m.userData.nivel] =
      (contagem[m.userData.nivel] || 0) + 1;
  });
  var chips = $("fNivel").children;
  for (var i = 0; i < chips.length; i++) {
    var n = chips[i].getAttribute("data-nivel");
    chips[i].setAttribute("aria-pressed", estado.niveis[n] ? "true" : "false");
    chips[i].querySelector(".n").textContent = contagem[n] || 0;
  }
}

function opcoes(select, valores, todas) {
  select.innerHTML = "<option value=''>" + todas + "</option>" +
    valores.map(function (v) {
      return "<option value='" + v + "'>" + v + "</option>";
    }).join("");
}

function preencherFiltros() {
  opcoes($("fArea"), areaLista, "Todas as areas");
  opcoes($("fContrato"), unicos(PESSOAS.map(function (p) { return p.contrato; })),
    "Todos os contratos");
  opcoes($("fStatus"), unicos(PESSOAS.map(function (p) { return p.status; })),
    "Todas as situacoes");
  opcoes($("fSexo"), unicos(PESSOAS.map(function (p) { return p.sexo; })), "Todos");
  $("fNivel").innerHTML = NIVEL_ORDEM.map(function (n) {
    return "<button class='chip' type='button' data-nivel='" + n +
      "' aria-pressed='true'>" + n + " <span class='n'>0</span></button>";
  }).join("");
  $("listaNomes").innerHTML = PESSOAS.map(function (p) {
    return "<option value='" + p.nome + "'>";
  }).join("");
}

function ligarEventos() {
  $("layout").addEventListener("change", function () {
    estado.layout = this.value;
    estado.selecionada = null;
    mostrarFicha(null);
    atualizar();
  });
  $("cor").addEventListener("change", function () {
    estado.cor = this.value;
    atualizar();
  });
  $("tamanho").addEventListener("change", function () {
    estado.tamanho = this.value;
    atualizar();
  });
  ["fArea", "fContrato", "fStatus", "fSexo"].forEach(function (id) {
    var chave = id.slice(1).toLowerCase();
    $(id).addEventListener("change", function () {
      estado[chave] = this.value;
      atualizar();
    });
  });
  $("fNivel").addEventListener("click", function (ev) {
    var botao = ev.target.closest ? ev.target.closest(".chip") : null;
    if (!botao) return;
    var n = botao.getAttribute("data-nivel");
    estado.niveis[n] = !estado.niveis[n];
    atualizar();
  });
  $("busca").addEventListener("input", function () {
    estado.busca = this.value.trim().toLowerCase();
    atualizar();
  });
  $("limpar").addEventListener("click", function () {
    estado.area = ""; estado.contrato = ""; estado.status = ""; estado.sexo = "";
    estado.busca = ""; estado.selecionada = null;
    NIVEL_ORDEM.forEach(function (n) { estado.niveis[n] = true; });
    ["fArea", "fContrato", "fStatus", "fSexo", "busca"].forEach(function (id) {
      $(id).value = "";
    });
    mostrarFicha(null);
    atualizar();
  });
  $("girar").addEventListener("click", function () {
    controles.autoRotate = !controles.autoRotate;
    this.setAttribute("aria-pressed", controles.autoRotate ? "true" : "false");
  });
  $("recuar").addEventListener("click", function () { vistaGeral(); });
  $("abEsq").addEventListener("click", function () { $("esq").classList.toggle("oculto"); });
  $("abDir").addEventListener("click", function () { $("dir").classList.toggle("oculto"); });

  render.domElement.addEventListener("pointermove", aoMover);
  render.domElement.addEventListener("pointerleave", esconderDica);
  render.domElement.addEventListener("click", aoClicar);
  render.domElement.addEventListener("dblclick", function () {
    estado.selecionada = null;
    mostrarFicha(null);
    atualizar();
  });
  window.addEventListener("keydown", function (ev) {
    if (ev.key === "r" || ev.key === "R") { vistaGeral(); }
  });
  window.addEventListener("resize", redimensionar);
}

function vistaGeral() {
  controles.target.set(0, 70, 0);
  camera.position.set(200, 165, 265);
  controles.update();
  desenharNumeros();
}

function redimensionar() {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  render.setSize(innerWidth, innerHeight);
  desenharNumeros();
}

function laco() {
  requestAnimationFrame(laco);
  controles.update();
  render.render(cena, camera);
}

function iniciar() {
  preparar();
  criarCena();
  criarEsferas();
  preencherFiltros();
  ligarEventos();
  vistaGeral();
  atualizar();
  mostrarFicha(null);
  laco();
}

try {
  iniciar();
} catch (erro) {
  document.getElementById("erro").style.display = "block";
  document.getElementById("erroMsg").innerHTML =
    "Se a tela ficou em branco, confira se os dois arquivos da pasta <code>lib</code> " +
    "continuam ao lado desta pagina.<br><br><b>" +
    (erro && erro.message ? erro.message : erro) + "</b>";
}
})();
</script>
</body>
</html>
"""

FAIXAS_SALARIAIS = {
    "Operacional": (1800, 3200),
    "Tecnico": (2600, 4800),
    "Analista": (3400, 6200),
    "Especialista": (4600, 8200),
    "Coordenador": (6200, 11000),
    "Gerencia": (9000, 18000),
    "Diretoria": (16000, 32000),
}


def aviso(texto):
    print("  " + texto)


def erro(texto):
    print("[ERRO] " + texto)
    sys.exit(1)


def carregar(caminho_csv):
    """Le o CSV e devolve a lista de pessoas, ja com chave curta."""
    if not os.path.isfile(caminho_csv):
        erro("nao achei o arquivo " + caminho_csv)

    # utf-8-sig come o BOM que o Excel precisa; o CSV foi gravado com ele
    with open(caminho_csv, "r", encoding="utf-8-sig", newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo, delimiter=";"))

    if not linhas:
        erro("o CSV esta vazio: " + caminho_csv)

    esperadas = [coluna for coluna, _ in MAPA]
    faltando = [c for c in esperadas if c not in linhas[0]]
    if faltando:
        erro("faltam colunas no CSV: " + ", ".join(faltando))

    pessoas = []
    for linha in linhas:
        p = {}
        for coluna, chave in MAPA:
            bruto = (linha.get(coluna) or "").strip()
            if chave in NUMERICOS:
                converter = NUMERICOS[chave]
                # o csv deste projeto grava numero com ponto decimal e sem
                # separador de milhar (2301.14). se aparecer virgula, o arquivo
                # foi regrado por outro software: ai o ponto e milhar
                try:
                    texto = bruto.replace("R$", "").replace("%", "").strip()
                    if "," in texto:
                        texto = texto.replace(".", "").replace(",", ".")
                    p[chave] = (int(float(texto)) if converter is int
                                else float(texto))
                except ValueError:
                    p[chave] = 0
            else:
                p[chave] = bruto
        pessoas.append(p)

    return pessoas


def conferir(pessoas):
    """Checagem simples antes de gerar a pagina. Erro aqui e erro na tela."""
    problemas = []
    ids = [p["m"] for p in pessoas]
    if len(set(ids)) != len(ids):
        problemas.append("ha matricula repetida")
    for p in pessoas:
        if not p["nome"] or not p["m"]:
            problemas.append("pessoa sem nome ou matricula")
            break
        if p["gestor"] and p["gestor"] not in ids:
            problemas.append(p["m"] + " aponta para gestor inexistente: " + p["gestor"])
            break
        if p["nivel"] not in FAIXAS_SALARIAIS:
            problemas.append(p["m"] + " com nivel fora do esperado: " + p["nivel"])
            break
    if problemas:
        erro("dado inconsistente: " + "; ".join(problemas))
    aviso("checagem ok: %d pessoas, %d areas, %d niveis"
          % (len(pessoas),
             len({p["area"] for p in pessoas}),
             len({p["nivel"] for p in pessoas})))


def montar_html(pessoas, caminho_html):
    dados = json.dumps(pessoas, ensure_ascii=True, separators=(",", ":"))
    faixas = json.dumps(FAIXAS_SALARIAIS, ensure_ascii=True, separators=(",", ":"))

    html = TEMPLATE.replace("__DADOS__", dados).replace("__FAIXAS__", faixas)
    html = html.replace("__N__", str(len(pessoas)))

    with open(caminho_html, "w", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write(html)

    return len(html)


def principal():
    pasta = os.path.dirname(os.path.abspath(__file__))
    caminho_csv = sys.argv[1] if len(sys.argv) > 1 else os.path.join(pasta, CSV_PADRAO)
    caminho_html = os.path.join(pasta, SAIDA_PADRAO)

    print("=" * 62)
    print(" MONTANDO A PAGEM 3D DO QUADRO DE PESSOAL")
    print("=" * 62)
    aviso("lendo " + caminho_csv)

    pessoas = carregar(caminho_csv)
    conferir(pessoas)

    aviso("escrevendo " + caminho_html)
    tamanho = montar_html(pessoas, caminho_html)

    aviso("pagina pronta: %s (%.0f KB)" % (os.path.basename(caminho_html), tamanho / 1024))
    aviso("abra com dois cliques. Nao precisa de servidor nem de internet.")
    print("=" * 62)


if __name__ == "__main__":
    principal()
