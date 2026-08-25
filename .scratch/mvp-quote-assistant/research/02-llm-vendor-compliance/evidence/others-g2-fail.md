# 证据：G2 未过或冲突的候选

**核验日：** 2026-08-25  
这些条目的共同结果：G2 不能记「通过」，一票否决，不进入识别对比。

## 智谱 bigmodel.cn

用户协议 https://docs.bigmodel.cn/cn/terms/user-agreement  

> 根据适用的法律，若我们对您的内容采取技术措施和其他必要措施进行处理，使得数据接收方无法重新识别特定个人且不能复原，或我们可能会对收集的信息进行匿名化的研究、统计分析和预测，用于改善大模型开放平台的内容和布局，为商业决策提供产品或服务支撑，以及改进我们的产品和服务（包括使用匿名数据进行机器学习或模型算法训练），按照相关法律法规规定，此类数据已不属于个人信息范畴，因此此类处理后的数据的使用无需另行征得您的同意。

> 为了改善我们向您提供的产品和服务的质量，我们可能利用您使用大模型平台或平台内模型过程中产生的数据，定位、维护和优化我们的产品和服务，但是您与智谱另有约定的除外。

> 在法律允许的范围内，您免费授予智谱及其关联公司非排他的、无地域限制的、永久的、免费的许可使用（包括存储、使用、复制、修订、编辑、发布、展示、翻译、分发上述信息或制作派生作品……）及可再许可第三方使用的权利

隐私政策存储地点 https://docs.bigmodel.cn/cn/terms/privacy-policy  

> 我们在中国境内运营中收集和产生的个人信息存储在中国境内。

Coding Plan 团队套餐 https://docs.bigmodel.cn/cn/terms/subscription-agreement-team 含「数据默认不用于模型训练」，但该协议适用于 Coding Plan 团队套餐，不是通用读图 API；订阅协议还限制额度不得接到自建后端。

## DeepSeek

隐私政策 https://cdn.deepseek.com/policies/zh-CN/deepseek-privacy-policy.html （开篇称适用于网页、App、SDK **和 API**）：

> 为向您提供连续、高质量的服务，在经安全加密技术处理和去标识化前提下，我们可能会将服务所收集的输入及对应输出，用于DeepSeek模型训练和服务的优化。如您拒绝将您的数据用于模型训练，可以在产品内通过关闭“数据用于优化体验”来选择退出

> 我们依照法律法规的规定，将在境内运营过程中收集和产生的您的个人信息存储于中华人民共和国境内。

开放平台服务协议 https://cdn.deepseek.com/policies/zh-CN/deepseek-open-platform-terms-of-service.html 第 4 条「输入与输出」规定权利归属，**没有**「不会用于训练」的肯定句。没有授权 ≠ 书面承诺。

## Kimi 开放平台（中国站）

帮助中心 https://www.kimi.ai/zh-hans/help/kimi-api/api-data-security  

> 不会。 通过 API 提交的用户数据（包括输入内容和模型输出）不会用于训练或改进 Kimi 的模型。你的数据仅用于完成当前 API 请求，不会为了训练目的而持久化存储。

服务协议 https://platform.kimi.com/docs/agreement/modeluse  

> 为了提升您使用本服务的体验，您授予我们一项免费的使用权，以在法律允许的范围内将您输入输出之内容及反馈用于模型服务优化。

冲突：帮助页不能压过合同。G2 记证据不足，按未过处理。

隐私政策 https://platform.kimi.com/docs/agreement/userprivacy  

> 我们将您的个人信息存储于中华人民共和国境内。

国际站 platform.kimi.ai 另写：除非书面约定，Customer Content 可用于改进服务。本轮不把国际站当中国站证据。

## 讯飞

开放平台隐私政策 https://www.xfyun.cn/doc/policy/privacy.html  

> 根据适用的法律法规，我们可能会对您的个人信息进行技术处理，使得根据该信息无法精确识别到用户个人，并对技术处理后的信息进行匿名化或去标识化的学术研究或统计分析（包括使用匿名化或去标识化后的语音信息进行模型算法的训练），以更好地提升产品功能和服务能力。

星火隐私政策 https://www.xfyun.cn/doc/spark/SparkPrivacyPolicy.html 讨论存储期限与服务器控制，未见足以让 G1 通过的「仅大陆处理客户输入」专条。

未把第三方站点转载的「星火接口服务协议」当作证据（非讯飞文档中心稳定 URL）。

## MiniMax

隐私政策 https://agent.minimaxi.com/doc/zh/privacy-policy.html  

> 1.7.2在经安全加密技术处理、去标识化且无法重新识别特定个人的前提下，我们可能会将输入内容、输出内容、行为信息进行分析和用于模型训练，以不断调整优化模型效果和产品体验。

用户协议里的 DPA 专节针对 Agent 任务数据（https://agent.minimaxi.com/doc/zh/terms-of-service.html），不能证明视觉推理 API 客户可签 DPA，也不能覆盖 1.7.2 的训练授权。
