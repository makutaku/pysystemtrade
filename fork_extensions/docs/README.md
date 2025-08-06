# pysystemtrade Documentation

Comprehensive documentation for the pysystemtrade systematic futures trading framework.

```mermaid
graph TB
    subgraph "Documentation Structure"
        Main[📚 Main Documentation]
        
        subgraph "Getting Started"
            Overview[📋 Project Overview]
            Install[⚙️ Installation Guide]  
            Quick[🚀 Quick Start]
        end
        
        subgraph "Architecture"
            HLD[🏗️ High-Level Design]
            LLD[🔧 Low-Level Design]
            SystemArch[📐 System Architecture]
        end
        
        subgraph "User Guides" 
            Trading[📈 Trading Strategies]
            DevWorkflow[👨‍💻 Development Workflow]
            Production[🏭 Production Setup]
        end
        
        subgraph "Reference"
            API[📖 API Reference]
            Examples[💡 Examples]
            Troubleshoot[🔍 Troubleshooting]
        end
    end
    
    Main --> Overview
    Main --> Install
    Main --> Quick
    
    Main --> HLD
    Main --> LLD  
    Main --> SystemArch
    
    Main --> Trading
    Main --> DevWorkflow
    Main --> Production
    
    Main --> API
    Main --> Examples
    Main --> Troubleshoot
    
    style Main fill:#e1f5fe
    style HLD fill:#fff3e0
    style LLD fill:#f3e5f5
    style Trading fill:#e8f5e8
```

## Documentation Organization

### **🎯 Getting Started**
- **[Project Overview](project-overview.md)** - What pysystemtrade is and what it does
- **[Installation Guide](installation.md)** - Complete setup for development and production
- **[Quick Start](guides/quick-start.md)** - Build your first trading system in 10 minutes

### **🏗️ Architecture Documentation**
Complete architectural specifications from strategic to implementation level:
- **[Architecture Overview](architecture/README.md)** - Comprehensive architectural documentation
- **[System Overview](architecture/system-overview.md)** - Core concepts and design principles
- **[High-Level Design (HLD)](architecture/hld/README.md)** - Strategic architecture and system design
- **[Low-Level Design (LLD)](lld/README.md)** - Detailed technical specifications

### **📚 User Guides**
Practical guides for development and production:
- **[User Guides Overview](guides/README.md)** - Complete guide navigation
- **[Trading Strategies](guides/trading-strategies.md)** - Built-in and custom trading rules
- **[Development Workflow](guides/development-workflow.md)** - Best practices and testing
- **[Production Setup](guides/production-setup.md)** - Going live with real trading

### **📖 Reference Materials**
- **[API Reference](api-reference.md)** - Key classes, methods, and interfaces
- **[Examples & Tutorials](examples/README.md)** - Real-world usage examples
- **[Troubleshooting Guide](troubleshooting.md)** - Common issues and solutions

## System Overview

```mermaid
graph LR
    subgraph "pysystemtrade Platform"
        subgraph "Data Layer"
            CSV[(CSV Files)]
            MongoDB[(MongoDB)]
            Parquet[(Parquet)]
            Arctic[(Arctic TS)]
        end
        
        subgraph "Core Framework"
            System[System Pipeline]
            Portfolio[Portfolio Manager]
            Risk[Risk Manager]
            Analytics[Analytics Engine]
        end
        
        subgraph "Execution Layer"
            Orders[Order Manager]
            Broker[Broker Interface]
            Production[Production Control]
        end
        
        subgraph "External Systems"
            IB[Interactive Brokers]
            DataFeeds[Market Data]
            Reporting[Reports & Alerts]
        end
    end
    
    CSV --> System
    MongoDB --> System
    Parquet --> System
    Arctic --> System
    
    System --> Portfolio
    System --> Risk
    System --> Analytics
    
    Portfolio --> Orders
    Risk --> Orders
    Orders --> Broker
    Broker --> Production
    
    Broker <--> IB
    System <--> DataFeeds
    Production --> Reporting
    
    classDef dataLayer fill:#e3f2fd
    classDef coreFramework fill:#f3e5f5  
    classDef executionLayer fill:#e8f5e8
    classDef externalSystems fill:#fff3e0
    
    class CSV,MongoDB,Parquet,Arctic dataLayer
    class System,Portfolio,Risk,Analytics coreFramework
    class Orders,Broker,Production executionLayer
    class IB,DataFeeds,Reporting externalSystems
```

## Key Features & Capabilities

```mermaid
mindmap
  root((pysystemtrade))
    Data Management
      Multiple Backends
      Real-time Feeds
      Historical Storage
      Data Quality
    Trading Strategies
      Built-in Rules
      Custom Strategies
      Portfolio Optimization
      Risk Management
    Production Trading
      Automated Execution
      Order Management
      Position Tracking
      P&L Monitoring
    Analytics & Research
      Backtesting Framework
      Performance Analytics
      Risk Metrics
      Reporting
```

## Documentation Principles

This documentation follows enterprise-grade standards:

- **📋 Comprehensive Coverage** - Complete system understanding from concepts to implementation
- **🎯 Practical Focus** - Real-world examples and production-ready patterns
- **🏗️ Architectural Clarity** - Clear separation between strategic and tactical documentation
- **📖 Easy Navigation** - Logical organization with cross-references and visual guides
- **🔄 Living Documentation** - Regularly updated to reflect system evolution
- **🎨 Visual Design** - Mermaid diagrams and structured presentations

## About This Documentation

This documentation is generated from comprehensive analysis of the pysystemtrade codebase and provides enterprise-grade architectural and implementation guidance. It complements the official documentation by focusing on practical usage, architectural patterns, and production deployment strategies.

- **Target Audience**: Developers, quants, system architects, and trading professionals
- **Scope**: Complete systematic trading platform implementation
- **Focus**: Production-ready patterns and enterprise architecture
- **Last Updated**: 2025-01-08
- **pysystemtrade Version**: 1.8.2+

---

**🚀 [Start with Project Overview](project-overview.md) | 🏗️ [Architecture Documentation](architecture/README.md) | 📚 [User Guides](guides/README.md)**