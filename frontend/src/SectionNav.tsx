import { APP_SECTIONS, type AppSectionId } from "./appSections";
import { useI18n } from "./i18n";

export function SectionNav({
  active,
  onSelect,
}: {
  active: AppSectionId;
  onSelect: (id: AppSectionId) => void;
}) {
  const { t } = useI18n();
  return (
    <nav aria-label="Ana menü">
      {APP_SECTIONS.map((section) => {
        const key = `nav.${section.id}.label`;
        const translated = t(key);
        return (
          <a
            key={section.id}
            className={`nav-item ${section.id === active ? "active" : ""}`}
            href={`#${section.id}`}
            aria-current={section.id === active ? "page" : undefined}
            onClick={(event) => {
              event.preventDefault();
              onSelect(section.id);
            }}
          >
            <span className="nav-icon" aria-hidden="true">{section.icon}</span>
            {translated === key ? section.label : translated}
          </a>
        );
      })}
    </nav>
  );
}
