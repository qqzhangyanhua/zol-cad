# 证据：阿里云百炼

**核验日：** 2026-08-25  
**SKU 口径：** 中国站按量付费视觉理解 API；不是 Coding Plan，不是国际站。

## G1

URL：https://terms.alicdn.com/legal-agreement/terms/common_platform_service/20230728213935489/20230728213935489.html  

> 6.2.8根据您与阿里云协商一致，阿里云将在您选定的阿里云百炼服务及模型服务所在国家或地区处理客户业务数据。阿里云恪守对客户的安全承诺，根据适用的法律法规保护客户业务数据。如您基于自身业务目的需要选择在中华人民共和国境外的阿里云百炼服务及模型服务处理客户业务数据，可能会导致您的客户业务数据出境。您作为客户业务数据的完全控制方应履行相应的数据出境合规义务，包括但不限于获取必要的授权同意、完成必要的信息披露、完成数据出境申报、与境外数据接收方签署协议等。

> 6.2.9. 如您选择本协议第5.3.条约定的三方模型API服务，您的客户业务数据的处理（包括但不限于：存储、删除、内容安全过滤等）以及部署模式（服务接入地和推理地等）以您和三方模型API服务商在相关服务协议中的约定为准。

URL：https://help.aliyun.com/zh/model-studio/what-is-model-studio  

> 目前提供以下地域的模型服务：华北2（北京）、美国（弗吉尼亚）、国际（新加坡）、德国（法兰克福）和日本（东京）地域  
> ……各地域的接入点（Endpoint/Base URL）不同，API Key 不通用，支持的模型、平台功能与价格也有所差异

同页代码示例列出北京 base_url：`https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1`

## G2

同服务协议：

> 6.2.5. 在遵循相关法律法规的基础上，我们承诺仅在提供服务所必需的最短时间内保留您的对话数据。我们不会在未获您授权的情况下使用您的对话数据训练我们的模型。

URL：https://help.aliyun.com/zh/model-studio/what-is-model-studio  

> 阿里云严格保护数据隐私，使用百炼按量付费 API 和 Token Plan 团队版时，不会将您的数据用于模型训练。

> Token Plan 个人版和 Coding Plan 的数据使用条款与上述承诺不同。使用 Coding Plan 期间，模型输入及模型生成的内容将用于服务改进与模型优化；Token Plan 个人版不包含团队版的"不使用数据训练模型"承诺。具体条款请参见 Token Plan 概述和 Coding Plan概述，以及《阿里云百炼服务协议》第 5.2 条。

URL：https://help.aliyun.com/zh/model-studio/privacy-notice  

> 阿里云严格保护数据隐私，绝不会将您的数据用于模型训练。

帮助页「绝不会」与 FAQ 的 SKU 例外同时存在。门槛判定以服务协议 6.2.5 + FAQ 的 SKU 边界为准：按量 API / Token Plan 团队版可引用；Coding Plan / 个人版不可引用。

## G3

URL：https://help.aliyun.com/zh/model-studio/related-agreements  

相关协议列表（本轮所见）：阿里云百炼服务协议；模型推理 SLA；体验功能特别说明；开源模型协议条款说明；三方模型服务协议和使用条款清单。**无 DPA。**

国际站 DPA（**不能**当作中国站百炼证据）：https://www.alibabacloud.com/help/zh/legal/latest/fe2cxg  

> This Addendum forms part of Alibaba Cloud International Website Membership Agreement or other equivalent agreement between You and Alibaba Cloud

中国站 Salesforce 产品有单独数据处理附录，产品名不包含百炼：https://help.aliyun.com/zh/sfoa/security-and-compliance/data-protection-addendum

## 区域与价格

- 视觉 token 公式：https://help.aliyun.com/zh/model-studio/vision-model/ — `h x w / (32 x 32) + 2`
- `qwen-vl-plus` 北京：输入 0.8 / 输出 2 元每百万 token — https://help.aliyun.com/zh/model-studio/qwen-vl-plus
- `qwen-vl-max` 北京：输入 1.6 / 输出 4 — https://help.aliyun.com/zh/model-studio/qwen-vl-max
- OSS `cn-beijing`：https://help.aliyun.com/zh/oss/user-guide/regions-and-endpoints

## 书面回函

待人工按 `06-dpa-inquiry-template.md` 发出。收到前 G3 保持「证据不足」。
