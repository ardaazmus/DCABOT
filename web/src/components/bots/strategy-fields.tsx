"use client";

import { useTranslations } from "next-intl";

import { WizardField } from "@/components/bots/wizard-field";
import type { WizardForm } from "@/lib/bots";

export type StrategySection = "entry" | "safety" | "exit";

/**
 * Strateji alanları (giriş + safety orders + çıkış); sihirbaz
 * adımlara böler (`include`), backtest tek sayfada gösterir.
 * Alan tanımları yalnız buradadır, kopya yoktur.
 */
export function StrategyFields({
  form,
  errors,
  minNotional,
  onChange,
  include = ["entry", "safety", "exit"],
  testIdPrefix = "strategy",
}: {
  form: WizardForm;
  errors: Partial<Record<string, string>>;
  minNotional?: string;
  onChange: <K extends keyof WizardForm>(key: K, value: WizardForm[K]) => void;
  include?: readonly StrategySection[];
  testIdPrefix?: string;
}) {
  const t = useTranslations("wizard");
  return (
    <>
      {include.includes("entry") ? (
        <>
          <fieldset>
            <legend className="text-sm font-medium">{t("directionLabel")}</legend>
            <div className="mt-2 flex gap-4 text-sm">
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  name={`${testIdPrefix}-direction`}
                  value="LONG"
                  checked={form.direction === "LONG"}
                  onChange={() => onChange("direction", "LONG")}
                  data-testid={`${testIdPrefix}-direction-long`}
                />
                {t("directionLong")}
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  name={`${testIdPrefix}-direction`}
                  value="SHORT"
                  checked={form.direction === "SHORT"}
                  onChange={() => onChange("direction", "SHORT")}
                  data-testid={`${testIdPrefix}-direction-short`}
                />
                {t("directionShort")}
              </label>
            </div>
            {errors.direction === undefined ? null : (
              <p role="alert" className="mt-1 text-sm text-loss">
                {errors.direction}
              </p>
            )}
          </fieldset>
          <fieldset>
            <legend className="text-sm font-medium">{t("marketLabel")}</legend>
            <div className="mt-2 flex gap-4 text-sm">
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  name={`${testIdPrefix}-market`}
                  value="SPOT"
                  checked={form.market === "SPOT"}
                  onChange={() => onChange("market", "SPOT")}
                  data-testid={`${testIdPrefix}-market-spot`}
                />
                {t("marketSpot")}
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  name={`${testIdPrefix}-market`}
                  value="FUTURES"
                  checked={form.market === "FUTURES"}
                  onChange={() => onChange("market", "FUTURES")}
                  data-testid={`${testIdPrefix}-market-futures`}
                />
                {t("marketFutures")}
              </label>
            </div>
            {errors.market === undefined ? null : (
              <p role="alert" className="mt-1 text-sm text-loss">
                {errors.market}
              </p>
            )}
          </fieldset>
          <WizardField
            decimal
            label={t("leverage")}
            value={form.leverage}
            onChange={(value) => onChange("leverage", value)}
            hint={t("leverageHint")}
            error={errors.leverage}
            placeholder={form.market === "FUTURES" ? "3" : "1"}
            inputMode="numeric"
            testId={`${testIdPrefix}-leverage`}
          />
          <WizardField
            decimal
            label={t("cooldown")}
            value={form.cooldown}
            onChange={(value) => onChange("cooldown", value)}
            hint={t("cooldownHint")}
            error={errors.cooldown}
            placeholder="0"
            inputMode="numeric"
            testId={`${testIdPrefix}-cooldown`}
          />
          <WizardField
            decimal
            label={t("minPrice")}
            value={form.minPrice}
            onChange={(value) => onChange("minPrice", value)}
            hint={t("minPriceHint")}
            error={errors.minPrice}
            testId={`${testIdPrefix}-min-price`}
          />
          <WizardField
            decimal
            label={t("maxPrice")}
            value={form.maxPrice}
            onChange={(value) => onChange("maxPrice", value)}
            hint={t("maxPriceHint")}
            error={errors.maxPrice}
            testId={`${testIdPrefix}-max-price`}
          />
          <WizardField
            decimal
            label={t("baseOrder")}
            value={form.baseOrder}
            onChange={(value) => onChange("baseOrder", value)}
            hint={minNotional === undefined ? undefined : t("baseOrderMin", { min: minNotional })}
            error={errors.baseOrder}
            testId={`${testIdPrefix}-base-order`}
          />
          <WizardField
            decimal
            label={t("maxActiveDeals")}
            value={form.maxActiveDeals}
            onChange={(value) => onChange("maxActiveDeals", value)}
            hint={t("maxActiveDealsHint")}
            error={errors.maxActiveDeals}
            placeholder={t("maxActiveDealsPlaceholder")}
            inputMode="numeric"
            testId={`${testIdPrefix}-max-active-deals`}
          />
        </>
      ) : null}
      {include.includes("safety") ? (
        <>
          <WizardField
          decimal
            label={t("safetyOrder")}
            value={form.safetyOrder}
            onChange={(value) => onChange("safetyOrder", value)}
            hint={t("safetyOrderHint")}
            error={errors.safetyOrder}
            testId={`${testIdPrefix}-safety-order`}
          />
          <WizardField
          decimal
            label={t("maxSafetyOrders")}
            value={form.maxSafetyOrders}
            onChange={(value) => onChange("maxSafetyOrders", value)}
            hint={t("maxSafetyOrdersHint")}
            error={errors.maxSafetyOrders}
            testId={`${testIdPrefix}-max-safety-orders`}
            inputMode="numeric"
          />
          <WizardField
          decimal
            label={t("maxActiveSafetyOrders")}
            value={form.maxActiveSafetyOrders}
            onChange={(value) => onChange("maxActiveSafetyOrders", value)}
            hint={t("maxActiveSafetyOrdersHint")}
            error={errors.maxActiveSafetyOrders}
            testId={`${testIdPrefix}-max-active-safety-orders`}
            placeholder={t("maxActivePlaceholder")}
            inputMode="numeric"
          />
          <WizardField
          decimal
            label={t("priceDeviation")}
            value={form.priceDeviation}
            onChange={(value) => onChange("priceDeviation", value)}
            hint={t("priceDeviationHint")}
            error={errors.priceDeviation}
            testId={`${testIdPrefix}-price-deviation`}
          />
          <WizardField
          decimal
            label={t("volumeScale")}
            value={form.volumeScale}
            onChange={(value) => onChange("volumeScale", value)}
            hint={t("volumeScaleHint")}
            error={errors.volumeScale}
            testId={`${testIdPrefix}-volume-scale`}
          />
          <WizardField
          decimal
            label={t("stepScale")}
            value={form.stepScale}
            onChange={(value) => onChange("stepScale", value)}
            hint={t("stepScaleHint")}
            error={errors.stepScale}
            testId={`${testIdPrefix}-safety-step-scale`}
          />
        </>
      ) : null}
      {include.includes("exit") ? (
        <>
          <WizardField
          decimal
            label={t("takeProfit")}
            value={form.takeProfit}
            onChange={(value) => onChange("takeProfit", value)}
            hint={t("takeProfitHint")}
            error={errors.takeProfit}
            testId={`${testIdPrefix}-take-profit`}
          />
          <WizardField
            decimal
            label={t("comboTakeProfit")}
            value={form.comboTakeProfit}
            onChange={(value) => onChange("comboTakeProfit", value)}
            hint={t("comboTakeProfitHint")}
            error={errors.comboTakeProfit}
            placeholder={t("comboTakeProfitPlaceholder")}
            testId={`${testIdPrefix}-combo-take-profit`}
          />
          <label className="flex items-center gap-2 text-sm font-medium">
            <input
              type="checkbox"
              checked={form.trailingEnabled}
              onChange={(event) => onChange("trailingEnabled", event.target.checked)}
              className="size-4 accent-[var(--accent)]"
            />
            {t("trailingEnable")}
          </label>
          {form.trailingEnabled ? (
            <WizardField
          decimal
              label={t("trailingTakeProfit")}
              value={form.trailingTakeProfit}
              onChange={(value) => onChange("trailingTakeProfit", value)}
              hint={t("trailingTakeProfitHint")}
              error={errors.trailingTakeProfit}
              testId={`${testIdPrefix}-trailing-take-profit`}
            />
          ) : null}
          <label className="flex items-center gap-2 text-sm font-medium">
            <input
              type="checkbox"
              checked={form.stopLossEnabled}
              onChange={(event) => onChange("stopLossEnabled", event.target.checked)}
              className="size-4 accent-[var(--accent)]"
            />
            {t("stopLossEnable")}
          </label>
          {form.stopLossEnabled ? (
            <WizardField
          decimal
              label={t("stopLoss")}
              value={form.stopLoss}
              onChange={(value) => onChange("stopLoss", value)}
              hint={t("stopLossHint")}
              error={errors.stopLoss}
              testId={`${testIdPrefix}-stop-loss`}
            />
          ) : null}
        </>
      ) : null}
    </>
  );
}
