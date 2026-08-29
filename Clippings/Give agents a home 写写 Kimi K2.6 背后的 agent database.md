---
title: "Give agents a home: 写写 Kimi K2.6 背后的 agent database"
source: "https://mp.weixin.qq.com/s/t3opQqSAccGVKtKFZdZyrQ"
author:
  - "[[dongxu]]"
published:
created: 2026-08-20
description:
tags:
  - "clippings"
---
dongxu 我世界的源代码 *2026年5月11日 21:22*

我前几个月写了几篇关于 Agent 需要什么样的 infrastructure 的文章： [如何做 AI Agent 喜欢的基础软件](https://mp.weixin.qq.com/s?__biz=MzI3MjI4Njk0Ng==&mid=2247484632&idx=1&sn=f6c802e94c0cd5cf3593b245e277fb3d&scene=21#wechat_redirect) ， [当我们在谈论 Agent Infra 时我们在谈论什么](https://mp.weixin.qq.com/s?__biz=MzI3MjI4Njk0Ng==&mid=2247484665&idx=1&sn=b08ce859156089648bc12c4d3311353b&scene=21#wechat_redirect) ，这几篇文章受到了很多朋友的喜爱，但它主要还是停留在理论层面，主要是提出了一些猜想。后来这几个月发生的事情大家也看见了，确实整个行业的发展正如同那两篇文章所写的一样，包括 Agent 的爆发（以 OpenClaw 和 Hermes 为代表），以及相关的 Agent Infra 的火爆，包括 Sandbox 和文件系统的复兴等等，不过所以如果说那几篇文章缺了什么的话，我觉得缺一个大规模的落地的例子。

最近有一件事让我挺开心的：首先，TiDB Cloud 正式成为了 Kimi K2.6 的供应商，为 Kimi Agent 建站服务提供动态的大规模的 Agent Database 支持。我因此有这样一个机会，能够跟 Kimi 团队深入合作，将之前那些看上去天马行空的想法真正落地了。下面我稍微说一说这个合作的一些细节（得到了 Kimi 团队的授权，比心♥️）。

那就先介绍一下 Kimi K2.6 的 Agent 场景吧。这个场景其实就是最典型的，由 Agent 帮助人类去完成端到端（End-to-End）在线应用的构建（生成代码），并形成一个真实可用的在线服务。

这个服务和其他的 AI 建站应用（例如众所周知的 Loveable）有所不同，Kimi K2.6 是从前端到后端都完全接管/托管，作为用户不用关心任何技术细节也不用有任何技术背景，只需要用文字表达需求。

这正是我在这篇 [文章](https://mp.weixin.qq.com/s?__biz=MzI3MjI4Njk0Ng==&mid=2247484632&idx=1&sn=f6c802e94c0cd5cf3593b245e277fb3d&scene=21#wechat_redirect) 中描述过的那种完全由 Agent 负责一切的场景，对于这类 Agent 应用，挑战其实并不在于代码生成的部分，而是在于后面的 hosting 的成本。

为什么这么说？如果这个应用的受众不是面向开发者，那用户群会变大非常多，因为不需要任何技术背景，门槛一下就低了很多。但是对于服务的提供方，其实更乐于看见这样的局面，原因在于：现在大多数 AI 模板服务的计费模式一般都是按月付费（订阅制），你可以想象一下：如果是一个重度消耗 Token 的用户，每一次请求都需要调用 LLM 来动态生成，这就会产生很大的算力消耗，对于模型厂商来说，从客户那里收到的订阅费，很大一部分都要转手支付给算力成本。

但对于网站托管，或者是类似 Kimi K2.6 这种一次性生成代码并持续在线提供服务的场景来说：

1. 算力的消耗其实主要集中在创建和生成代码的那几下。
2. 服务运行起来以后，厂商仍然可以按月收客户的钱。
3. 托管应用所要支付的基础设施（主要是 web 服务器，带宽和数据库）成本比起算力的成本，厂商利润空间就大了很多。

所以在这种背景下，主要的挑战在于用户的数量以及支撑这种自助服务的Infra 成本，比如在短短一周时间内，可能就有上千万个站点被创建出来，如果按照传统的云服务或者数据库的定价，像这些独立的、灵活的站点，不可能为每一个网站都提供一个真实的实例去 host 一个 Postgres 或者 RDS，这样整体的成本肯定是算不下来的。但是如果你使用像类似 SQLite 这样的嵌入式数据库，虽然可以降低一些门槛，但也需要花很多的时间精力去处理备份、恢复、高可用等等，在成百上千万规模的小型的由 agent 动态创建的网站应用的行为下，维护这些 SQLite 不是一件简单的事情。

可能大家会说，为什么 Kimi 选择 TiDB，并没有选择名气更大的 NeonDB 和 Supabase 这类名气可能更大的 Serverless 的 Database 方案，归根结底，使用这套方案还是成本问题。例如像 Supabase 这种模式，唯一的问题在于，如果每一个 Agent 配一个 Supabase 的 PostgreSQL，想象下上百万个实例的情况下，成本会直接爆炸。

另外一方面，Kimi 团队也试过用一个大型的 PostgreSQL 实例，然后在内部通过多 Schema 的方式来进行租户的隔离，根据实际的测试结果，单个实例大概在万级规模时就扛不住了，更不用说复杂的流控，故障半径控制和数据隔离问题。

其实我去年下半年就反复想这件事：Agent-native 时代的数据 Infra 竞争，跟过去 30 年都不太一样，过去比的是单点性能：谁的 TPS 高、谁的延迟低，谁支持单数据库更大的容量。。。但现在不是，现在比的是当：

1. 海量长尾租户，尽管请求量不大，但是全都要求在线
2. LLM 即席改 Schema，必须支持分支和多版本
3. 需要应对无法预测的爆发流量
4. 让 AI 在秒级别随时动态创建/销毁，以及动态生成访问的 SQL

这四件事同时发生的时候，谁能提供最顺畅的体验？这是个完全不一样的赛道。

我们过去几个月和 Kimi 工程团队合作中学到了很多，总结一下，Kimi K2.6 Agent 建站的项目能做成，大概是三个最核心的战略决策：

**1：最小化 Agent 使用 Infra 工具时的摩擦**

每个任务和站点独立隔离，由 Agent 创建和使用，用的时候能秒级创建。这一条成立，后面才有得聊。TiDB Cloud 的 Warm Pool + Scale-To-zero，让 Agent 在 1 秒内拿到 fully prepared 的数据库实例。

Agent 生成应用，整个交付链路本身就是几分钟的事——用户输入需求、Agent 写代码、调用数据库、写数据、启动应用。如果数据库 provisioning 占去其中几分钟，Agent 就得在自己代码里写 retry / poll / wait 那一套。这个负担其实不该由 Agent 来扛。

**2：对 Agent 生成服务所使用的技术栈尽可能统一**

人类工程师觉得方便，对 LLM 来说这直接关系到生成代码的成功率，少跨一个系统就少一类 bug，多用 Skill 中写好的技术栈（例如开发框架的建议和脚手架）和最佳实践，而不是每次靠思考和抽卡，也大大提升了生成的代码变成服务的稳定性。

3. **极致的低成本**

因为放弃了类似 Supabase 和 Neon 那样的真实的数据库实例的分配和管理，TiDB 其实引入了一层虚拟数据库界面，因为这类 Agent 的建站场景大量的请求是长尾的，事实上没有请求的事情，是不需要真实的分配数据库实例的，只需要让这个 Agent / 终端用户有请求的时候，我 ‘假装’ 后端是一个独立的数据库即可，最极端的情况下，其实整个平台只需要一个常驻的 DB Session Gateway 服务负责维持数据库连接即可，其他所有的资源都可以变成弹性的。下面是这个架构和 Supabase 等传统 Serverless 数据库的架构对比：

![图片](https://mmbiz.qpic.cn/mmbiz_png/AQatuicdEC6WiciaQIp4WRicibC0vZTgFVvI4nevjRGXRfwicZibIlbHbosAY9RF4YpXibGibeia5QQfwibib0qCMFbECZWmQib6Q5cHRkKc0LibQ2tMicXwNA/640?wx_fmt=png&from=appmsg#imgIndex=0)

这个是传统的 Serverless 数据库面对 Agent 场景的架构：每个 Sandbox 分配一个真实的数据库实例，为了成本控制，冷却的时候会被回收，很难保证 7x24 永远在线，而且由于是真实的数据库实例，数量大了成本也很难控制（想象一下，几千万个 Supabase？）

![图片](https://mmbiz.qpic.cn/sz_mmbiz_png/AQatuicdEC6X03AeOuwWr0LpVBlnJUAhJMP0qtCp2VZr75pCb2eViaqamQ0OZTsia5SKsS64lYNG8DNESavo37Dx7kE7XVBvm3pvicqZ72qjyIc/640?wx_fmt=png&from=appmsg#imgIndex=1)

这是 TiDB Cloud 的架构，并没有真实的数据库实例存在，一切都是虚拟的，但是在 Sandbox 中的 Agent 看来它仍然是拥有一个个完整的独立的数据库，实际上在物理层面，数据是由底层的一个大型的封装了对象存储的分布式 KV 数据库提供存储服务，这个底层的大型数据库在逻辑层面上自动处理了数据可见性的隔离和冷热分离。这样在 Agent 层面就不会有类似实例被回收，休眠或者连接中断等不好的体验。

这样的架构转变将整个数据库平台的弹性能力提升了一个台阶，换来的是在 Agent 场景的数据使用成本的数量级规模的下降。

最后的结果也很美妙，在写本文的时候我随手给我家做了个简单的家庭留言板，大概不到 10分钟，从前端到后端，从开发到托管上线，一切顺滑如丝。

Kimi 对 TiDB Cloud 的评价也很高：选 TiDB 的核心原因不在某一个单点指标的极致——而在于 **"per-tenant 多租隔离、统一栈、即时弹性"** 这三件事同时做到位时，它是少数几个把每一项都"够用且顺手"的系统。

**行业层面：这不是孤例，It's happening**

过去 12 个月，我们陪跑过国内外很多 AI Agent 团队的基建选型。我们发现以前一个产品和服务扛亿级用户，一个 app 扛的是亿级会话。现在模式变了：一个用户身边可能有 10 个 甚至 100 个 Agent 在跑，每个都需要自己的状态和数据。。。但是包括 Kimi 在内的一些 AI Agent 作为商业模式的团队采用的架构都收敛到同一个范式： **one agent, one sandbox，one storage，one database** 。

Agent 商业化的场景才是刚刚开始，上半场大家在讨论谁的模型更聪明、谁的 Agent 推理更长。下半场是 **我认为竞争的核心是： Agent 交付出来的东西和结果，在真实用户面前能不能稳定跑起来，持续的交付。Kimi 和** **TiDB** **的合作就是一个绝佳的例子，模型厂商如何通过好的基础设施服务，快速/高效的提供更多的价值。**

当然 TiDB Cloud 只是数据库的场景，也许下次就是 TiDB Filesystem 或者 TiDB Sandbox？当下的时代，真的是一切皆有可能，也请拭目以待吧。

![图片](https://mmbiz.qpic.cn/sz_mmbiz_jpg/AQatuicdEC6U98wqFUzv1x6sGBgzjBYkOb4LjrfPKptjZogcQehibsiaz04ibCICfEexpS57RzAXLEFvlWjcoPjk5tGKVMAyxZGbXEs3H2ic9FwA/640?wx_fmt=jpeg&from=appmsg#imgIndex=2)