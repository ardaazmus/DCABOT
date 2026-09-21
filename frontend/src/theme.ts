export type Theme = "dark" | "light";

export const THEME_STORAGE_KEY = "dcabot-theme";

function isTheme(value: unknown): value is Theme {
  return value === "dark" || value === "light";
}

/**
 * Faz 11 tasarım kararı madde 8: kayıtlı tema > sistem tercihi > koyu varsayılan.
 * `stored` localStorage okuması, `prefersLight` matchMedia eşleşmesidir;
 * ikisi de enjekte edilir ki saf ve test edilebilir kalsın.
 */
export function resolveTheme(
  stored: string | null,
  prefersLight: () => boolean,
): Theme {
  if (isTheme(stored)) return stored;
  return prefersLight() ? "light" : "dark";
}

export function applyTheme(root: HTMLElement, theme: Theme): void {
  root.dataset.theme = theme;
}
