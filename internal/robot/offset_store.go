package robot

// StreamOffsetStore 持久化各平台长轮询游标（下一条待处理消息的 update_id）。
//
// 背景：Telegram getUpdates 只在请求里带 offset 时才会跳过已消费的消息。
// 游标若只存在内存里，服务一重启 offset 就会回到 0，Telegram 会把整段
// 未处理积压重播一遍，机器人就会把旧消息逐条重答——也就是「没人叫它，它自己吵」。
// 实现方通常是 internal/database 的机器人游标表，跨重启保留游标。
type StreamOffsetStore interface {
	GetRobotStreamOffset(platform string) (int64, error)
	SaveRobotStreamOffset(platform string, offset int64) error
}
