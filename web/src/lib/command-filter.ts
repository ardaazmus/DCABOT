export type CommandItem = {
  id: string;
  label: string;
  /** İkincil metin: rota ya da parite durumu gibi. */
  hint?: string;
};

function fold(text: string): string {
  return text.toLocaleLowerCase("tr");
}

/**
 * Komut paleti filtrelemesi: sorgu, öğe etiketi ya da ipucunda geçiyorsa
 * eşleşir. Boş sorgu ilk `limit` öğeyi döndürür. Sıralama korunur.
 */
export function filterCommands(
  items: readonly CommandItem[],
  query: string,
  limit = 8,
): CommandItem[] {
  const needle = fold(query.trim());
  if (!needle) return items.slice(0, limit);
  return items
    .filter(
      (item) => fold(item.label).includes(needle) || (item.hint !== undefined && fold(item.hint).includes(needle)),
    )
    .slice(0, limit);
}
