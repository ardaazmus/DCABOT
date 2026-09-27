import { Fragment } from "react";

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
  let lastGroup = "";
  return (
    <nav aria-label="Ana menü">
      {APP_SECTIONS.map((section) => {
        const key = `nav.${section.id}.label`;
        const translated = t(key);
        const showGroup = section.group !== "" && section.group !== lastGroup;
        lastGroup = section.group;
        return (
          <Fragment key={section.id}>
            {showGroup && (
              <p className="nav-group-label" aria-hidden="true">
                {section.group}
              </p>
            )}
            <a
              className={`nav-item ${section.id === active ? "active" : ""}`}
              href={`#/${section.id}`}
              aria-current={section.id === active ? "page" : undefined}
              onClick={(event) => {
                event.preventDefault();
                onSelect(section.id);
              }}
            >
              <span className="nav-icon" aria-hidden="true">{section.icon}</span>
              {translated === key ? section.label : translated}
            </a>
          </Fragment>
        );
      })}
    </nav>
  );
}
