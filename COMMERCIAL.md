# JySecAI 商用與授權邊界

JySecAI 可以收費營運，但「可收費」與「擁有所有上游程式碼的獨占權」是兩件不同的事。

## 可以採用的商業模式

- 代管 SaaS：按 Professional／Business 月費、年費或 credits 收費。
- 私有化部署：按節點、Worker、組織或年度授權收費。
- Enterprise Sovereign：客戶 VPC／內網、SSO、私有模型、私有 Worker、長期稽核與 SLA。
- 專業服務：授權安全驗證、客製工作流、規則包、教育訓練、維護與報告。

`platform/` 已提供 Stripe Checkout、Customer Portal、Webhook 驗證、方案 entitlement、月 credits、並發限制與保存期限。實際售價由 Stripe Price 管理，不硬編碼於程式。

## Apache-2.0 義務

本倉庫含有源自 CyberStrikeAI 的 Apache-2.0 程式。散布修改版時應：

1. 附上 Apache-2.0 授權全文。
2. 保留原始著作權與 attribution。
3. 明確標示已修改的部分。
4. 保留適用的 NOTICE 內容。
5. 不暗示上游作者為 JySecAI 背書。

Apache-2.0 允許商業使用、修改、代管與收費，也允許將自己的額外模組採不同授權；但不可移除上游權利與聲明。

## 品牌

JySecAI 名稱、Jy 立體標誌與「Jy 技術團隊」識別和原始碼授權分離。第三方即使依法使用 Apache-2.0 程式，也不因此自動取得 Jy 品牌使用權。正式營運前應進行商標檢索與必要註冊。

## 外部引擎

Strix、Promptfoo、PyRIT、Giskard、ART、Humanbound 與未來引擎由部署者獨立安裝或透過 adapter 呼叫。發行包含這些元件的映像前，必須逐一核對當時版本的授權、NOTICE、商標與商用條款。`plutoxAI` 未提供足以確認可複製的完整來源與授權，因此本專案不包含其程式或素材。

## 安全與責任

商業客戶必須提供測試授權範圍、有效期限、允許操作與核准者。高風險行為不得透過方案升級繞過 HITL、Scope、RBAC 或稽核。合約應清楚規範目標資產、資料保存、事件處理、責任限制與分包 Worker。

本文件是工程與產品邊界說明，不是特定司法管轄區的法律意見。正式銷售前應由律師審閱最終授權、商標、服務條款、隱私政策與資料處理協議。
