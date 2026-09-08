INSERT INTO jy_tenant_subscriptions (tenant_id, plan_id)
VALUES ('dev-tenant', 'business')
ON CONFLICT (tenant_id) DO UPDATE
SET plan_id = EXCLUDED.plan_id,
    status = 'active',
    updated_at = NOW();
