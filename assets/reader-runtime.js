(() => {
  const body = document.body;
  const state = {
    lastTrigger: null,
    activeSourceId: null,
  };

  const supportsCssEscape = window.CSS && typeof CSS.escape === "function";
  const cssEscape = (value) => (supportsCssEscape ? CSS.escape(String(value)) : String(value).replace(/["\\]/g, "\\$&"));
  const all = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const first = (selector, root = document) => root.querySelector(selector);
  const visiblePanelSelector = [
    "#term-panel",
    "#term-popover",
    "#figure-panel",
    "#figure-drawer",
    "[data-term-panel]",
    "[data-figure-panel]",
    ".drawer",
    "dialog[open]",
  ].join(",");

  function setPanelVisible(panel, visible) {
    if (!panel) return;
    if (panel.tagName === "DIALOG") {
      if (visible && !panel.open) panel.showModal();
      if (!visible && panel.open) panel.close();
      return;
    }
    panel.setAttribute("aria-hidden", visible ? "false" : "true");
    panel.hidden = !visible;
    panel.classList.toggle("is-open", visible);
  }

  function closePanels(options = {}) {
    all(visiblePanelSelector).forEach((panel) => setPanelVisible(panel, false));
    all('[aria-expanded="true"]').forEach((trigger) => trigger.setAttribute("aria-expanded", "false"));
    all(".is-term-active,.is-figure-active").forEach((item) => item.classList.remove("is-term-active", "is-figure-active"));
    if (options.restoreFocus !== false && state.lastTrigger && typeof state.lastTrigger.focus === "function") {
      state.lastTrigger.focus({ preventScroll: true });
      state.lastTrigger.scrollIntoView({ block: "nearest", inline: "nearest" });
    }
  }

  function setChapter(chapterId, options = {}) {
    if (!chapterId) return;
    const buttons = all("button[data-chapter],a[data-chapter],[role='tab'][data-chapter]");
    const panels = all("[data-chapter-panel]");
    const target = first(`[data-chapter-panel="${cssEscape(chapterId)}"],#${cssEscape(chapterId)}`);
    if (!target) return;

    panels.forEach((panel) => {
      const active = panel === target;
      if (active) {
        panel.setAttribute("data-active", "true");
        panel.hidden = false;
      } else {
        panel.removeAttribute("data-active");
        panel.hidden = true;
      }
    });
    buttons.forEach((button) => {
      const active = button.dataset.chapter === chapterId;
      button.setAttribute("aria-current", active ? "true" : "false");
      button.setAttribute("aria-selected", active ? "true" : "false");
    });

    const firstBlock = first(".reading-block,[data-source-id]", target);
    if (firstBlock) updateSideNote(firstBlock);
    if (options.scroll !== false) target.scrollIntoView({ block: "start", inline: "nearest" });
    document.dispatchEvent(new CustomEvent("learning-site:chapter-change", { detail: { chapterId } }));
  }

  function setLanguageMode(mode) {
    if (!mode) return;
    body.dataset.mode = mode;
    all("button[data-mode],a[data-mode],[role='tab'][data-mode]").forEach((button) => {
      const active = button.dataset.mode === mode;
      button.setAttribute("aria-pressed", active ? "true" : "false");
      button.setAttribute("aria-selected", active ? "true" : "false");
    });
    const activeBlock = state.activeSourceId
      ? first(`[data-source-id="${cssEscape(state.activeSourceId)}"]`)
      : first(".reading-block.is-active,[data-source-id].is-active");
    if (activeBlock) updateSideNote(activeBlock);
    document.dispatchEvent(new CustomEvent("learning-site:language-change", { detail: { mode } }));
  }

  function updateSideNote(block) {
    if (!block) return;
    all(".reading-block.is-active,[data-source-id].is-active").forEach((item) => item.classList.remove("is-active"));
    block.classList.add("is-active");
    const sourceId = block.dataset.sourceId || block.id || "";
    state.activeSourceId = sourceId;

    const noteTitle = block.dataset.noteTitle || first("[data-note-title]", block)?.textContent || "";
    const noteBody = block.dataset.noteBody || first("[data-note-body]", block)?.textContent || "";
    const noteText = block.dataset.note || first("[data-note-text]", block)?.textContent || noteBody || "";
    const sideNote = first("#side-note,[data-side-note]");
    const sideTitle = first("#side-note-title,[data-side-note-title],[data-note-title]", sideNote || document);
    const sideText = first("#side-note-text,[data-side-note-text]", sideNote || document);
    const sideBody = first("#side-note-body,[data-side-note-body],[data-note-body]", sideNote || document);
    const sideLink = first("#side-note-link,[data-side-note-link]", sideNote || document);
    if (sideTitle && noteTitle) sideTitle.textContent = noteTitle;
    if (sideText && noteText) sideText.textContent = noteText;
    if (sideBody && noteText) sideBody.textContent = noteText;
    if (sideLink && block.id) {
      sideLink.href = `#${block.id}`;
      sideLink.textContent = "回到原文";
    }
    document.dispatchEvent(new CustomEvent("learning-site:source-focus", { detail: { sourceId } }));
  }

  function fillText(root, selector, value) {
    const node = first(selector, root);
    if (node) node.textContent = value || "";
  }

  function openTerm(termId, trigger) {
    const terms = window.LEARNING_SITE_TERMS || {};
    const item = terms[termId];
    const panel = first("#term-panel,#term-popover,[data-term-panel]");
    if (!item || !panel) return;
    closePanels({ restoreFocus: false });
    state.lastTrigger = trigger;
    trigger.classList.add("is-term-active");
    trigger.setAttribute("aria-expanded", "true");

    fillText(panel, "[data-term-title],#term-title", item.title || trigger.textContent.trim());
    fillText(panel, "[data-term-field],#term-field", item.field || item.definition || "");
    fillText(panel, "[data-term-plain],#term-plain", item.plain || "");
    fillText(panel, "[data-term-paper],#term-paper", item.paper || "");
    fillText(panel, "[data-term-use],#term-use", item.use || "");
    fillText(panel, "[data-term-misread],#term-misread", item.misread || "");
    const sourceId = item.source_id || item.sourceId || trigger.closest("[data-source-id]")?.dataset.sourceId;
    const back = first("[data-term-back],#term-back", panel);
    if (back && sourceId) {
      const block = first(`[data-source-id="${cssEscape(sourceId)}"]`);
      back.href = block?.id ? `#${block.id}` : "#";
      back.textContent = "回到原词";
    }
    setPanelVisible(panel, true);
    if (window.innerWidth <= 900) {
      requestAnimationFrame(() => {
        trigger.scrollIntoView({ block: "start", inline: "nearest" });
      });
    }
    document.dispatchEvent(new CustomEvent("learning-site:term-open", { detail: { termId, sourceId } }));
  }

  function openFigure(figureId, trigger) {
    const figures = window.LEARNING_SITE_FIGURES || {};
    const item = figures[figureId];
    const panel = first("#figure-panel,#figure-drawer,[data-figure-panel]");
    if (!item || !panel) return;
    closePanels({ restoreFocus: false });
    state.lastTrigger = trigger;
    trigger.classList.add("is-figure-active");
    trigger.setAttribute("aria-expanded", "true");

    fillText(panel, "[data-figure-title],#figure-title", item.title || trigger.textContent.trim());
    fillText(panel, "[data-figure-note],#figure-note", item.note || "");
    const image = first("[data-figure-img],#figure-img", panel);
    if (image && item.path) {
      image.src = item.path;
      image.alt = item.alt || item.title || "图表放大视图";
    }
    const sourceId = item.source_id || item.sourceId || (Array.isArray(item.source_ids) ? item.source_ids[0] : "");
    const back = first("[data-figure-back],#figure-back", panel);
    if (back && sourceId) {
      const block = first(`[data-source-id="${cssEscape(sourceId)}"]`);
      back.href = block?.id ? `#${block.id}` : "#";
      back.textContent = "回到原文";
    }
    setPanelVisible(panel, true);
    document.dispatchEvent(new CustomEvent("learning-site:figure-open", { detail: { figureId, sourceId } }));
  }

  function answerReview(choice) {
    const card = choice.closest("[data-review],.review-card,[data-quiz],.quiz-card");
    if (!card) return;
    const reviewId = card.dataset.review || card.dataset.quiz || card.id || "";
    const choiceId = choice.dataset.reviewChoice || choice.dataset.quizChoice || choice.value || choice.textContent.trim();
    const feedback = first(".review-feedback,[data-review-feedback],.quiz-feedback,[data-quiz-feedback],[aria-live]", card);
    const configured = choice.dataset.feedback
      || window.LEARNING_SITE_REVIEW_FEEDBACK?.[reviewId]?.[choiceId]
      || window.LEARNING_SITE_QUIZ_FEEDBACK?.[reviewId]?.[choiceId]
      || "";
    const sourceId = choice.dataset.sourceId || card.dataset.sourceId;
    const block = sourceId ? first(`[data-source-id="${cssEscape(sourceId)}"]`) : first(".reading-block,[data-source-id]", card.closest("[data-chapter-panel]") || document);
    if (feedback) {
      feedback.textContent = configured;
      if (block?.id) {
        const link = document.createElement("a");
        link.href = `#${block.id}`;
        link.textContent = " 回到原文证据";
        link.className = "review-evidence-link";
        link.addEventListener("click", () => {
          all(".is-review-target").forEach((item) => item.classList.remove("is-review-target"));
          block.classList.add("is-review-target");
          updateSideNote(block);
        });
        feedback.appendChild(link);
      }
    }
    if (block) updateSideNote(block);
    document.dispatchEvent(new CustomEvent("learning-site:review-answer", { detail: { reviewId, choiceId, sourceId } }));
    document.dispatchEvent(new CustomEvent("learning-site:quiz-answer", { detail: { quizId: reviewId, choiceId, sourceId } }));
  }

  document.addEventListener("click", (event) => {
    const chapter = event.target.closest("button[data-chapter],a[data-chapter],[role='tab'][data-chapter]");
    if (chapter) {
      event.preventDefault();
      setChapter(chapter.dataset.chapter);
      return;
    }
    const mode = event.target.closest("button[data-mode],a[data-mode],[role='tab'][data-mode]");
    if (mode) {
      event.preventDefault();
      setLanguageMode(mode.dataset.mode);
      return;
    }
    const term = event.target.closest(".term[data-term],[data-term-id],[data-open-drawer='term']");
    if (term) {
      event.preventDefault();
      event.stopPropagation();
      openTerm(term.dataset.term || term.dataset.termId, term);
      return;
    }
    const figure = event.target.closest("[data-figure],[data-figure-id]");
    if (figure) {
      event.preventDefault();
      openFigure(figure.dataset.figure || figure.dataset.figureId, figure);
      return;
    }
    const reviewChoice = event.target.closest("[data-review-choice],[data-quiz-choice]");
    if (reviewChoice) {
      event.preventDefault();
      answerReview(reviewChoice);
      return;
    }
    const close = event.target.closest("[data-close],[data-close-panel],.close-drawer");
    if (close) {
      event.preventDefault();
      closePanels();
      return;
    }
    const readingBlock = event.target.closest(".reading-block,[data-source-id]");
    if (readingBlock) updateSideNote(readingBlock);
  });

  document.addEventListener("focusin", (event) => {
    const readingBlock = event.target.closest?.(".reading-block,[data-source-id]");
    if (readingBlock) updateSideNote(readingBlock);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closePanels();
  });

  const initialChapter = first("button[data-chapter][aria-current='true'],[role='tab'][data-chapter][aria-selected='true']")?.dataset.chapter
    || first("[data-chapter-panel][data-active='true']")?.dataset.chapterPanel
    || first("[data-chapter-panel]")?.dataset.chapterPanel;
  if (initialChapter) setChapter(initialChapter, { scroll: false });
  const initialMode = first("button[data-mode][aria-pressed='true'],[role='tab'][data-mode][aria-selected='true']")?.dataset.mode || body.dataset.mode;
  if (initialMode) setLanguageMode(initialMode);

  window.LearningSiteReader = {
    setChapter,
    setLanguageMode,
    updateSideNote,
    closePanels,
    openTerm,
    openFigure,
    answerReview,
    answerQuiz: answerReview,
  };
})();
