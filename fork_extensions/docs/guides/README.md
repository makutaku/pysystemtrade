# User Guides

Practical guides for using and developing with pysystemtrade.

```mermaid
flowchart LR
    Start([New User]) --> QS[Quick Start]
    QS --> TS[Trading Strategies]
    TS --> DW[Development Workflow]
    DW --> Advanced[Advanced Topics]
    
    QS --> Install[Installation Guide]
    Install --> Config[Configuration]
    Config --> Production[Production Setup]
    
    subgraph "Getting Started"
        QS
        Install
        Config
    end
    
    subgraph "Development"
        TS
        DW
        Advanced
    end
    
    subgraph "Production"
        Production
        Monitoring[Monitoring]
        Troubleshooting[Troubleshooting]
    end
    
    Advanced --> Production
    Production --> Monitoring
    Monitoring --> Troubleshooting
```

## Available Guides

### **Getting Started**
- **[Quick Start Guide](quick-start.md)** - Get up and running in 10 minutes
- **[Installation Guide](../installation.md)** - Complete setup instructions
- **[Project Overview](../project-overview.md)** - Understanding pysystemtrade

### **Trading & Strategies**  
- **[Trading Strategies Guide](trading-strategies.md)** - Built-in and custom strategies
- **[Configuration Guide](configuration.md)** - System configuration and parameters
- **[Risk Management Guide](risk-management.md)** - Position limits and risk controls

### **Development**
- **[Development Workflow](development-workflow.md)** - Development best practices
- **[Testing Guide](testing.md)** - Unit testing and backtesting
- **[API Reference](../api-reference.md)** - Key classes and methods

### **Production**
- **[Production Setup](production-setup.md)** - Going live with real trading
- **[Interactive Brokers Guide](interactive-brokers.md)** - Broker integration
- **[Monitoring & Alerts](monitoring.md)** - System health and alerting
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

### **Advanced Topics**
- **[Data Management](data-management.md)** - Storage backends and sources
- **[Custom Extensions](custom-extensions.md)** - Extending the framework
- **[Performance Optimization](performance-optimization.md)** - Scaling and optimization

## Guide Structure

Each guide follows a consistent structure:
- **Overview** - What you'll learn
- **Prerequisites** - Required knowledge and setup
- **Step-by-step Instructions** - Clear, actionable steps
- **Examples** - Real-world code examples  
- **Troubleshooting** - Common issues and solutions
- **Next Steps** - Where to go from here

## Navigation

- **[← Back to Main Documentation](../README.md)**
- **[Architecture Documentation →](../architecture/README.md)**
- **[API Reference →](../api-reference.md)**

---

*These guides provide practical, hands-on instructions for effectively using pysystemtrade in development and production environments.*