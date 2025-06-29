sequenceDiagram
    participant User as 用户
    participant SDK as CatLink SDK
    participant API as CatLink API
    participant Device as 猫砂盒设备

    User->>SDK: 创建客户端并认证
    SDK->>API: 登录请求
    API-->>SDK: 返回认证令牌
    
    User->>SDK: 获取设备列表
    SDK->>API: 请求设备列表
    API-->>SDK: 返回设备数据
    
    User->>SDK: 启用调试模式
    SDK->>Device: enable_debug(True)
    
    User->>SDK: 更新设备详情
    SDK->>API: token/litterbox/info
    API-->>SDK: 返回完整设备信息
    SDK->>SDK: 记录调试日志
    
    User->>SDK: 获取除臭剂状态
    SDK-->>User: deodorant_countdown: X天
    
    User->>SDK: 获取调试信息
    SDK-->>User: 返回所有原始数据和属性