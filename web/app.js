"use strict";

const steps = ["Briefing", "Sumário", "Conteúdo", "Revisão", "Exportação"];
const form = document.querySelector("#brief-form");
const workflow = document.querySelector("#workflow");
const status = document.querySelector("#status");
const example = document.querySelector("#example");
const navigation = [...document.querySelectorAll("nav button")];
const storageKey = "criador-editorial-v1";
const sample = {
  theme: "Marketing de conteúdo", audience: "Pequenos empreendedores",
  kind: "Apostila", level: "Introdutório", pages: 24, count: 4,
};

let project = { brief: null, outline: [], modules: [], reviews: [] };
let step = 0;
let busy = false;

try {
  const saved = localStorage.getItem(storageKey);
  if (saved) {
    project = JSON.parse(saved);
    step = maxStep();
  }
} catch {
  announce("O projeto salvo neste navegador está indisponível.", true);
}
fill(project.brief || {});

function fill(values) {
  for (const [key, value] of Object.entries(values)) form.elements[key].value = value;
}

function maxStep() {
  if (project.modules.length && project.modules.every(module => module.approved)) return 4;
  if (project.reviews.length) return 3;
  if (project.modules.length) return 2;
  return project.outline.length ? 1 : 0;
}

function save() {
  try {
    localStorage.setItem(storageKey, JSON.stringify(project));
  } catch {
    announce("Seu navegador não conseguiu salvar o projeto. Mantenha esta página aberta.", true);
  }
}

function announce(message, error = false) {
  status.textContent = message;
  status.hidden = !message;
  status.classList.toggle("error", error);
}

function element(tag, content, className) {
  const item = document.createElement(tag);
  if (content) item.textContent = content;
  if (className) item.className = className;
  return item;
}

function action(text, callback, className = "primary") {
  const button = element("button", text, className);
  button.type = "button";
  button.addEventListener("click", callback);
  return button;
}

function go(next, focus = true) {
  step = next;
  render();
  if (focus) {
    const heading = document.querySelector(next ? "#workflow h2" : "#brief-title");
    heading.tabIndex = -1;
    heading.focus();
  }
}

async function api(name, payload) {
  const response = await fetch("/api/" + name, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.error || "Não foi possível concluir a operação.");
  }
  return name === "export" ? response.blob() : response.json();
}

async function run(callback) {
  if (busy) return;
  announce("");
  busy = true;
  const controls = [...document.querySelectorAll("button, input, textarea, select")]
    .filter(control => !control.disabled);
  controls.forEach(control => { control.disabled = true; });
  try {
    await callback();
  } catch (error) {
    announce(error.message, true);
  } finally {
    busy = false;
    controls.forEach(control => { control.disabled = false; });
    renderNavigation();
  }
}

function renderNavigation() {
  const furthest = maxStep();
  document.querySelector("#breadcrumb").textContent = steps[step];
  const progress = document.querySelector(".steps");
  progress.replaceChildren();
  steps.forEach((title, index) => {
    const current = step === index;
    const completed = index < furthest;
    const item = element("li", null, completed ? "complete" : "");
    item.append(element("span", completed ? "✓" : String(index + 1)), title);
    item.firstChild.setAttribute("aria-hidden", "true");
    const button = navigation[index];
    button.disabled = busy || index > furthest;
    button.removeAttribute("aria-current");
    if (current) {
      button.setAttribute("aria-current", "step");
      item.setAttribute("aria-current", "step");
    }
    progress.append(item);
  });
}

function render() {
  renderNavigation();
  document.querySelector("#brief-panel").hidden = step !== 0;
  workflow.hidden = step === 0;
  workflow.replaceChildren();
  if (step === 0) return;

  const headings = [
    null,
    ["☷", "Sumário do material", "Confira a sequência de aprendizagem e a estimativa de páginas."],
    ["✎", "Conteúdo dos módulos", "Edite os rascunhos de exemplo antes de enviar para revisão."],
    ["✓", "Revisão editorial", "Confira as sugestões automáticas e aprove os módulos após sua leitura."],
    ["↓", "Exportar material", "Baixe o documento Word com o sumário e os módulos aprovados."],
  ];
  const [icon, title, description] = headings[step];
  const heading = element("div", null, "panel-heading");
  const badge = element("span", icon, "panel-icon");
  badge.setAttribute("aria-hidden", "true");
  const copy = element("div");
  const h2 = element("h2", title);
  h2.id = "workflow-title";
  workflow.setAttribute("aria-labelledby", h2.id);
  copy.append(h2, element("p", description));
  heading.append(badge, copy);
  workflow.append(heading);
  const footer = element("div", null, "panel-footer");

  if (step === 1) renderOutline(footer);
  if (step === 2) renderEditor(footer);
  if (step === 3) renderReview(footer);
  if (step === 4) renderExport(footer);
  workflow.append(footer);
}

function moduleCard(module) {
  const card = element("article", null, "module");
  card.append(element("h3", `Módulo ${module.id} · ${module.title}`));
  workflow.append(card);
  return card;
}

function renderOutline(footer) {
  for (const entry of project.outline) {
    const card = moduleCard(entry);
    card.append(element("p", `Objetivo de aprendizagem — ${entry.goal}.`));
    card.append(element("p", `${entry.pages} pág. estimadas`));
  }
  const hasContent = project.modules.length > 0;
  const next = action(hasContent ? "Abrir conteúdo →" : "Gerar conteúdo →", () => {
    if (hasContent) return go(2);
    return run(async () => {
      const { modules } = await api("write", { brief: project.brief, outline: project.outline });
      project.modules = modules;
      save();
      go(2);
    });
  });
  footer.append(element("span", `${project.brief.pages} páginas planejadas`), next);
}

function renderEditor(footer) {
  for (const module of project.modules) {
    const card = moduleCard(module);
    const titleLabel = element("label", "Título do módulo");
    const title = element("input");
    title.maxLength = 250;
    title.value = module.title;
    titleLabel.append(title);
    const label = element("label", "Texto do módulo");
    const field = element("textarea");
    field.maxLength = 60000;
    field.value = module.content;
    label.append(field);
    card.append(titleLabel, label);
    for (const [input, key] of [[title, "title"], [field, "content"]]) {
      input.addEventListener("input", () => {
        module[key] = input.value;
        module.approved = false;
        project.reviews = [];
        save();
        renderNavigation();
      });
    }
  }
  footer.append(element("span", "As edições são salvas neste navegador."), action("Revisar conteúdo →", () => run(async () => {
    const { reviews } = await api("review", { modules: project.modules });
    project.reviews = reviews;
    save();
    go(3);
  })));
}

function renderReview(footer) {
  const countApproved = () => project.modules.filter(module => module.approved).length;
  const counter = element("span");
  const next = action("Ir para exportação →", () => go(4));
  const update = () => {
    const approved = countApproved();
    counter.textContent = `${approved} de ${project.modules.length} módulos aprovados`;
    next.disabled = approved !== project.modules.length;
    renderNavigation();
  };
  for (const [index, module] of project.modules.entries()) {
    const card = moduleCard(module);
    const notes = project.reviews[index].notes;
    const list = element("ul");
    for (const note of notes.length ? notes : ["Nenhuma sugestão nas verificações automáticas."]) {
      list.append(element("li", note));
    }
    const details = element("details");
    details.append(element("summary", "Ler texto do módulo"), element("div", module.content, "review-text"));
    const toggle = action("", () => {
      module.approved = !module.approved;
      refreshApproval();
      update();
      save();
    }, "secondary");
    const refreshApproval = () => {
      toggle.textContent = module.approved ? "Revogar aprovação" : "Aprovar módulo";
      toggle.setAttribute("aria-label", `${toggle.textContent} ${module.id}`);
      toggle.setAttribute("aria-pressed", String(module.approved));
    };
    refreshApproval();
    card.append(list, details, toggle);
  }
  footer.append(counter, next);
  update();
}

function renderExport(footer) {
  footer.append(element("span", project.brief.theme), action("Baixar Word (.docx) ↓", () => run(async () => {
    const blob = await api("export", { brief: project.brief, modules: project.modules });
    const url = URL.createObjectURL(blob);
    const link = element("a");
    link.href = url;
    link.download = "material.docx";
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    announce("O arquivo Word está pronto.");
  })));
}

navigation.forEach((button, index) => button.addEventListener("click", () => {
  announce("");
  go(index);
}));

example.addEventListener("click", () => {
  fill(sample);
  announce("Exemplo carregado no formulário. Gere o sumário para começar.");
  go(0);
});

form.addEventListener("submit", event => {
  event.preventDefault();
  const brief = Object.fromEntries(new FormData(form));
  brief.theme = brief.theme.trim();
  brief.audience = brief.audience.trim();
  brief.pages = Number(brief.pages);
  brief.count = Number(brief.count);
  if (project.outline.length && Object.keys(brief).every(key => brief[key] === project.brief[key])) {
    go(1);
    return;
  }
  if (project.modules.length && !window.confirm("Alterar o briefing substituirá os módulos atuais. Continuar?")) return;
  run(async () => {
    const { outline } = await api("plan", { brief });
    project = { brief, outline, modules: [], reviews: [] };
    fill(brief);
    save();
    go(1);
  });
});

render();
