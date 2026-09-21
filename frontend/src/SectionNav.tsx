import { APP_SECTIONS, type AppSectionId } from "./appSections";

export function SectionNav({
  active,
  onSelect,
}: {
  active: AppSectionId;
  onSelect: (id: AppSectionId) => void;
}) {
  return (
    <nav aria-label="Ana menü">
      {APP_SECTIONS.map((section) => (
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
          {section.label}
        </a>
      ))}
    </nav>
  );
}
