// El desplegable con el diseño del sistema donde el navegador no sabe dibujarlo
// (B-00-011). Ver templates/_desplegable_propio.html: ahí está el porqué.
(function () {
  const forzado = document.documentElement.hasAttribute("data-desplegable-propio");
  if (!forzado && window.CSS && CSS.supports("appearance", "base-select")) return;

  let serie = 0;
  const mejorados = [];

  function mejorar(select) {
    if (select.dataset.desplegable || select.multiple || select.size > 1) return;
    select.dataset.desplegable = "1";
    serie += 1;
    const prefijo = "desplegable-" + serie;

    const caja = document.createElement("div");
    caja.className = "desplegable";
    select.before(caja);
    caja.append(select);
    select.classList.add("desplegable__nativo");
    select.tabIndex = -1;
    select.setAttribute("aria-hidden", "true");

    const boton = document.createElement("button");
    boton.type = "button";
    boton.id = prefijo + "-boton";
    boton.className = "desplegable__boton";
    boton.setAttribute("role", "combobox");
    boton.setAttribute("aria-haspopup", "listbox");
    boton.setAttribute("aria-expanded", "false");
    boton.setAttribute("aria-controls", prefijo + "-lista");
    const rotulo = select.labels && select.labels[0];
    if (rotulo) {
      rotulo.id = rotulo.id || prefijo + "-rotulo";
      boton.setAttribute("aria-labelledby", rotulo.id);
      rotulo.addEventListener("click", function (evento) { evento.preventDefault(); boton.focus(); });
    }
    for (const nombre of ["aria-invalid", "aria-describedby"]) {
      if (select.hasAttribute(nombre)) boton.setAttribute(nombre, select.getAttribute(nombre));
    }

    const lista = document.createElement("ul");
    lista.id = prefijo + "-lista";
    lista.className = "desplegable__lista";
    lista.setAttribute("role", "listbox");
    lista.hidden = true;
    caja.append(boton, lista);

    let activa = -1;
    let tecleado = "";
    let pausaTecleo = null;

    function opciones() {
      return Array.from(lista.querySelectorAll('[role="option"]'));
    }

    function pintar() {
      const elegida = select.options[select.selectedIndex];
      const texto = elegida ? elegida.textContent.trim() : "";
      if (boton.textContent !== texto) boton.textContent = texto;
      boton.disabled = select.disabled;
    }

    function construir() {
      lista.replaceChildren();
      for (const hijo of select.children) {
        if (hijo.tagName === "OPTGROUP") {
          const grupo = document.createElement("li");
          grupo.className = "desplegable__grupo";
          grupo.setAttribute("role", "presentation");
          grupo.textContent = hijo.label;
          lista.append(grupo);
          for (const opcion of hijo.children) lista.append(item(opcion));
        } else if (hijo.tagName === "OPTION") {
          lista.append(item(hijo));
        }
      }
    }

    function item(opcion) {
      const li = document.createElement("li");
      li.id = prefijo + "-opcion-" + opcion.index;
      li.setAttribute("role", "option");
      li.dataset.indice = opcion.index;
      li.textContent = opcion.textContent.trim();
      li.setAttribute("aria-selected", opcion.selected ? "true" : "false");
      if (opcion.disabled) li.setAttribute("aria-disabled", "true");
      return li;
    }

    function marcar(indice) {
      const todas = opciones();
      activa = indice;
      for (const li of todas) li.classList.toggle("desplegable__activa", Number(li.dataset.indice) === indice);
      const li = todas.find(function (o) { return Number(o.dataset.indice) === indice; });
      if (li) {
        boton.setAttribute("aria-activedescendant", li.id);
        li.scrollIntoView({ block: "nearest" });
      }
    }

    function mover(paso) {
      const habilitadas = opciones().filter(function (o) { return !o.hasAttribute("aria-disabled"); });
      if (!habilitadas.length) return;
      let lugar = habilitadas.findIndex(function (o) { return Number(o.dataset.indice) === activa; });
      if (paso === Infinity) lugar = habilitadas.length - 1;
      else if (paso === -Infinity) lugar = 0;
      else lugar = Math.min(Math.max(lugar + paso, 0), habilitadas.length - 1);
      marcar(Number(habilitadas[lugar].dataset.indice));
    }

    function abrir() {
      if (select.disabled || !lista.hidden) return;
      construir();
      lista.hidden = false;
      boton.setAttribute("aria-expanded", "true");
      marcar(select.selectedIndex);
      document.addEventListener("pointerdown", afuera, true);
    }

    function cerrar() {
      if (lista.hidden) return;
      lista.hidden = true;
      boton.setAttribute("aria-expanded", "false");
      boton.removeAttribute("aria-activedescendant");
      document.removeEventListener("pointerdown", afuera, true);
    }

    function afuera(evento) {
      if (!caja.contains(evento.target)) cerrar();
    }

    function elegir(indice) {
      const opcion = select.options[indice];
      if (!opcion || opcion.disabled) return;
      if (select.selectedIndex !== indice) {
        select.selectedIndex = indice;
        select.dispatchEvent(new Event("input", { bubbles: true }));
        select.dispatchEvent(new Event("change", { bubbles: true }));
      }
      pintar();
      cerrar();
      boton.focus();
    }

    function teclear(letra) {
      window.clearTimeout(pausaTecleo);
      tecleado += letra.toLowerCase();
      pausaTecleo = window.setTimeout(function () { tecleado = ""; }, 600);
      const sinAcento = function (texto) { return texto.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase(); };
      const buscado = sinAcento(tecleado);
      const hallada = Array.from(select.options).find(function (o) {
        return !o.disabled && sinAcento(o.textContent.trim()).startsWith(buscado);
      });
      if (!hallada) return;
      if (lista.hidden) elegir(hallada.index);
      else marcar(hallada.index);
    }

    boton.addEventListener("click", function () { lista.hidden ? abrir() : cerrar(); });
    boton.addEventListener("keydown", function (evento) {
      const abierta = !lista.hidden;
      switch (evento.key) {
        case "ArrowDown":
        case "ArrowUp":
          evento.preventDefault();
          if (!abierta) abrir();
          else mover(evento.key === "ArrowDown" ? 1 : -1);
          break;
        case "Home":
        case "End":
          if (abierta) { evento.preventDefault(); mover(evento.key === "Home" ? -Infinity : Infinity); }
          break;
        case "Enter":
        case " ":
          evento.preventDefault();
          if (abierta) elegir(activa); else abrir();
          break;
        case "Escape":
          if (abierta) { evento.preventDefault(); cerrar(); }
          break;
        case "Tab":
          cerrar();
          break;
        default:
          if (evento.key.length === 1 && !evento.ctrlKey && !evento.metaKey && !evento.altKey) teclear(evento.key);
      }
    });
    lista.addEventListener("pointerdown", function (evento) { evento.preventDefault(); });
    lista.addEventListener("click", function (evento) {
      const li = evento.target.closest('[role="option"]');
      if (li) elegir(Number(li.dataset.indice));
    });
    select.addEventListener("change", pintar);
    select.addEventListener("focus", function () { boton.focus(); });
    select.form && select.form.addEventListener("reset", function () { window.setTimeout(pintar); });
    // Otros guiones cambian las opciones o el estado del select.
    new MutationObserver(function () {
      pintar();
      if (!lista.hidden) { construir(); marcar(select.selectedIndex); }
    }).observe(select, { childList: true, subtree: true, attributes: true, attributeFilter: ["disabled", "selected", "aria-invalid"] });

    pintar();
    mejorados.push(pintar);
  }

  function mejorarEn(raiz) {
    if (raiz.matches && raiz.matches("select")) mejorar(raiz);
    if (raiz.querySelectorAll) for (const select of raiz.querySelectorAll("select")) mejorar(select);
  }

  document.addEventListener("DOMContentLoaded", function () {
    mejorarEn(document);
    // Los formularios que suman campos (ítems del lote, filas de la portada).
    new MutationObserver(function (cambios) {
      for (const cambio of cambios) for (const nodo of cambio.addedNodes) if (nodo.nodeType === 1) mejorarEn(nodo);
    }).observe(document.body, { childList: true, subtree: true });
    // Un guion que asigna `select.value` sin avisar: el botón lo alcanza igual.
    window.setInterval(function () { for (const pintar of mejorados) pintar(); }, 500);
  });
})();
