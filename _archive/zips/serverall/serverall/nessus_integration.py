"""
Nessus API 集成模块 - 企业级漏洞扫描集成
为企业级渗透测试系统提供专业的Nessus漏洞扫描能力
"""

import requests
import json
import time
import base64
from typing import Dict, List, Any, Optional
import asyncio
import logging

class NessusIntegration:
    """Nessus API 集成类"""
    
    def __init__(self, nessus_url: str, access_key: str, secret_key: str):
        """
        初始化Nessus集成
        
        Args:
            nessus_url: Nessus服务器URL (e.g., https://localhost:8834)
            access_key: Nessus API访问密钥
            secret_key: Nessus API密钥
        """
        self.nessus_url = nessus_url.rstrip('/')
        self.access_key = access_key
        self.secret_key = secret_key
        self.headers = {
            'X-ApiKeys': f'accessKey={access_key}; secretKey={secret_key}',
            'Content-Type': 'application/json'
        }
        self.scan_cache = {}
        self.logger = logging.getLogger(__name__)
        
    async def test_connection(self) -> Dict[str, Any]:
        """测试Nessus连接"""
        try:
            response = requests.get(
                f"{self.nessus_url}/scans",
                headers=self.headers,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message": "Nessus连接成功",
                    "scans_count": len(response.json().get('scans', []))
                }
            else:
                return {
                    "status": "error",
                    "message": f"Nessus连接失败: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Nessus连接异常: {str(e)}"
            }
    
    async def create_scan(self, target: str, scan_name: str = "自动化渗透扫描", 
                         scan_template: str = "advanced"):
        """
        创建Nessus扫描任务
        
        Args:
            target: 目标URL或IP
            scan_name: 扫描名称
            scan_template: 扫描模板 (basic, advanced, web_app, discovery)
        """
        templates = {
            "basic": "basic",
            "advanced": "advanced",
            "web_app": "webapp",
            "discovery": "discovery"
        }
        
        template_uuid = templates.get(scan_template, "advanced")
        
        scan_config = {
            "uuid": template_uuid,
            "settings": {
                "name": scan_name,
                "description": f"自动化渗透扫描 - {target}",
                "text_targets": target,
                "enabled": True,
                "launch": "ON_DEMAND",
                "folder_id": 1,
                "scanner_id": 1,
                "policy_id": 0,
                "starttime": None,
                "rrules": None
            }
        }
        
        try:
            response = requests.post(
                f"{self.nessus_url}/scans",
                headers=self.headers,
                json=scan_config,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                scan_data = response.json()
                scan_id = scan_data['scan']['id']
                
                # 缓存扫描信息
                self.scan_cache[scan_id] = {
                    'target': target,
                    'name': scan_name,
                    'status': 'created'
                }
                
                return {
                    "status": "success",
                    "scan_id": scan_id,
                    "message": f"扫描任务创建成功: {scan_name}"
                }
            else:
                return {
                    "status": "error",
                    "message": f"扫描创建失败: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"扫描创建异常: {str(e)}"
            }
    
    async def start_scan(self, scan_id: int) -> Dict[str, Any]:
        """启动Nessus扫描"""
        try:
            response = requests.post(
                f"{self.nessus_url}/scans/{scan_id}/launch",
                headers=self.headers,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                self.scan_cache[scan_id]['status'] = 'running'
                return {
                    "status": "success",
                    "message": f"扫描 {scan_id} 已启动",
                    "scan_uuid": response.json().get('scan_uuid')
                }
            else:
                return {
                    "status": "error", 
                    "message": f"扫描启动失败: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"扫描启动异常: {str(e)}"
            }
    
    async def get_scan_status(self, scan_id: int) -> Dict[str, Any]:
        """获取扫描状态"""
        try:
            response = requests.get(
                f"{self.nessus_url}/scans/{scan_id}",
                headers=self.headers,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                scan_data = response.json()
                status = scan_data['info']['status']
                progress = scan_data.get('info', {}).get('progress', 0)
                
                return {
                    "status": "success",
                    "scan_status": status,
                    "progress": progress,
                    "details": scan_data
                }
            else:
                return {
                    "status": "error",
                    "message": f"获取扫描状态失败: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "error", 
                "message": f"获取扫描状态异常: {str(e)}"
            }
    
    async def wait_for_scan_completion(self, scan_id: int, 
                                     check_interval: int = 30, 
                                     timeout: int = 3600) -> Dict[str, Any]:
        """等待扫描完成"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status_result = await self.get_scan_status(scan_id)
            
            if status_result['status'] == 'success':
                scan_status = status_result['scan_status']
                
                if scan_status == 'completed':
                    return {
                        "status": "success",
                        "message": "扫描完成",
                        "scan_id": scan_id
                    }
                elif scan_status == 'canceled':
                    return {
                        "status": "error",
                        "message": "扫描被取消"
                    }
                elif scan_status == 'aborted':
                    return {
                        "status": "error", 
                        "message": "扫描被中止"
                    }
                else:
                    # 扫描进行中，继续等待
                    progress = status_result.get('progress', 0)
                    self.logger.info(f"扫描进度: {progress}%")
                    await asyncio.sleep(check_interval)
            else:
                return status_result
        
        return {
            "status": "error",
            "message": f"扫描超时 (>{timeout}秒)"
        }
    
    async def get_scan_results(self, scan_id: int) -> Dict[str, Any]:
        """获取扫描结果"""
        try:
            # 获取扫描详情
            response = requests.get(
                f"{self.nessus_url}/scans/{scan_id}",
                headers=self.headers,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                scan_data = response.json()
                vulnerabilities = scan_data.get('vulnerabilities', [])
                
                # 分析漏洞严重性
                severity_counts = {
                    "critical": 0,
                    "high": 0, 
                    "medium": 0,
                    "low": 0,
                    "info": 0
                }
                
                for vuln in vulnerabilities:
                    severity = vuln.get('severity', 0)
                    if severity >= 4:
                        severity_counts["critical"] += 1
                    elif severity == 3:
                        severity_counts["high"] += 1
                    elif severity == 2:
                        severity_counts["medium"] += 1
                    elif severity == 1:
                        severity_counts["low"] += 1
                    else:
                        severity_counts["info"] += 1
                
                # 获取详细的漏洞信息
                detailed_vulns = []
                for vuln in vulnerabilities[:50]:  # 限制数量避免过大
                    vuln_id = vuln.get('plugin_id')
                    if vuln_id:
                        vuln_details = await self.get_vulnerability_details(scan_id, vuln_id)
                        if vuln_details['status'] == 'success':
                            detailed_vulns.append(vuln_details['vulnerability'])
                
                return {
                    "status": "success",
                    "scan_info": scan_data.get('info', {}),
                    "vulnerabilities": vulnerabilities,
                    "detailed_vulnerabilities": detailed_vulns,
                    "severity_summary": severity_counts,
                    "total_vulnerabilities": len(vulnerabilities)
                }
            else:
                return {
                    "status": "error",
                    "message": f"获取扫描结果失败: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"获取扫描结果异常: {str(e)}"
            }
    
    async def get_vulnerability_details(self, scan_id: int, plugin_id: int) -> Dict[str, Any]:
        """获取漏洞详细信息"""
        try:
            response = requests.get(
                f"{self.nessus_url}/scans/{scan_id}/plugins/{plugin_id}",
                headers=self.headers,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "vulnerability": response.json()
                }
            else:
                return {
                    "status": "error",
                    "message": f"获取漏洞详情失败: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"获取漏洞详情异常: {str(e)}"
            }
    
    async def export_scan_report(self, scan_id: int, 
                               format_type: str = "html") -> Dict[str, Any]:
        """导出扫描报告"""
        try:
            export_config = {
                "format": format_type
            }
            
            response = requests.post(
                f"{self.nessus_url}/scans/{scan_id}/export",
                headers=self.headers,
                json=export_config,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                export_data = response.json()
                file_id = export_data.get('file')
                
                # 等待报告生成
                await asyncio.sleep(10)
                
                # 下载报告
                download_response = requests.get(
                    f"{self.nessus_url}/scans/{scan_id}/export/{file_id}/download",
                    headers=self.headers,
                    verify=False,
                    timeout=60
                )
                
                if download_response.status_code == 200:
                    # 保存报告文件
                    filename = f"nessus_scan_{scan_id}_report.{format_type}"
                    with open(filename, 'wb') as f:
                        f.write(download_response.content)
                    
                    return {
                        "status": "success",
                        "message": f"报告导出成功: {filename}",
                        "file_path": filename,
                        "format": format_type
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"报告下载失败: {download_response.status_code}"
                    }
            else:
                return {
                    "status": "error",
                    "message": f"报告导出请求失败: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"报告导出异常: {str(e)}"
            }
    
    async def full_scan_workflow(self, target: str, scan_name: str = "自动化渗透扫描") -> Dict[str, Any]:
        """完整的扫描工作流"""
        self.logger.info(f"开始Nessus扫描工作流 - 目标: {target}")
        
        # 1. 创建扫描
        create_result = await self.create_scan(target, scan_name)
        if create_result['status'] != 'success':
            return create_result
        
        scan_id = create_result['scan_id']
        self.logger.info(f"扫描创建成功: {scan_id}")
        
        # 2. 启动扫描
        start_result = await self.start_scan(scan_id)
        if start_result['status'] != 'success':
            return start_result
        
        self.logger.info("扫描已启动，等待完成...")
        
        # 3. 等待扫描完成
        wait_result = await self.wait_for_scan_completion(scan_id)
        if wait_result['status'] != 'success':
            return wait_result
        
        self.logger.info("扫描已完成，获取结果...")
        
        # 4. 获取扫描结果
        results = await self.get_scan_results(scan_id)
        
        # 5. 导出报告
        report_result = await self.export_scan_report(scan_id, "html")
        
        return {
            "status": "success",
            "scan_id": scan_id,
            "target": target,
            "scan_results": results,
            "report": report_result,
            "message": "Nessus扫描工作流完成"
        }
    
    def generate_summary_report(self, scan_results: Dict[str, Any]) -> str:
        """生成扫描摘要报告"""
        if scan_results['status'] != 'success':
            return f"扫描失败: {scan_results.get('message', '未知错误')}"
        
        results = scan_results.get('scan_results', {})
        severity = results.get('severity_summary', {})
        total = results.get('total_vulnerabilities', 0)
        
        report = f"""
=== Nessus 扫描报告摘要 ===

目标: {scan_results.get('target', '未知')}
扫描ID: {scan_results.get('scan_id', '未知')}

漏洞统计:
- 总计: {total} 个漏洞
- 严重: {severity.get('critical', 0)} 个
- 高危: {severity.get('high', 0)} 个  
- 中危: {severity.get('medium', 0)} 个
- 低危: {severity.get('low', 0)} 个
- 信息: {severity.get('info', 0)} 个

前10个重要漏洞:
"""
        
        vulnerabilities = results.get('detailed_vulnerabilities', [])[:10]
        for i, vuln in enumerate(vulnerabilities, 1):
            plugin_info = vuln.get('plugin', {})
            report += f"\n{i}. {plugin_info.get('plugin_name', '未知')}"
            report += f"\n   严重性: {plugin_info.get('severity', '未知')}"
            report += f"\n   描述: {plugin_info.get('description', '无描述')[:100]}...\n"
        
        return report

# 多Nessus服务器配置
nessus_servers_config = {
    "nessus_server_1": {
        "nessus_url": "https://localhost:8834",
        "access_key": "e8088618f5d23a93a76127670b09dc4e5ce9e087f3ad1fb4f5d24c49941b7a12",
        "secret_key": "6feb13d1c518a1e0960a53520a136605abdc068995e69eccd7541e6adf2cdbe1"
    },
    "nessus_server_2": {
        "nessus_url": "https://localhost:8834", 
        "access_key": "30621a6d39e501a21bc31adb1aa40f633127e0deef08cd094ff20f80d5565f8c",
        "secret_key": "5716d0ca6fb04b6a0c235d1f57756e08c0847b869fd50c5313e8f34e34e45856"
    }
}

class NessusManager:
    """Nessus管理器 - 支持多服务器负载均衡"""
    
    def __init__(self, servers_config: Dict[str, Any] = None):
        self.servers_config = servers_config or nessus_servers_config
        self.servers = {}
        self.server_status = {}
        
        # 初始化服务器实例
        for server_name, config in self.servers_config.items():
            self.servers[server_name] = NessusIntegration(
                nessus_url=config["nessus_url"],
                access_key=config["access_key"],
                secret_key=config["secret_key"]
            )
    
    async def check_server_health(self, server_name: str) -> bool:
        """检查服务器健康状态"""
        try:
            server = self.servers.get(server_name)
            if not server:
                return False
            
            # 测试认证
            status = await server.test_connection()
            health = status.get('status') == 'success'
            
            self.server_status[server_name] = {
                'healthy': health,
                'last_check': datetime.now().isoformat(),
                'message': status.get('message', '')
            }
            return health
            
        except Exception as e:
            print(f"[-] 检查服务器 {server_name} 健康状态失败: {e}")
            self.server_status[server_name] = {
                'healthy': False,
                'last_check': datetime.now().isoformat(),
                'error': str(e)
            }
            return False
    
    async def get_best_server(self) -> Optional[NessusIntegration]:
        """获取最佳可用服务器"""
        # 检查所有服务器状态
        health_checks = []
        for server_name in self.servers:
            health = await self.check_server_health(server_name)
            health_checks.append((server_name, health))
        
        # 选择健康的服务器
        healthy_servers = [name for name, healthy in health_checks if healthy]
        
        if not healthy_servers:
            print("[-] 没有可用的Nessus服务器")
            return None
        
        # 简单轮询选择
        selected_server = healthy_servers[0]
        print(f"[+] 选择服务器: {selected_server}")
        return self.servers[selected_server]
    
    async def distributed_scan(self, targets: List[str], scan_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """分布式扫描 - 多服务器负载均衡"""
        results = {}
        
        # 获取可用服务器列表
        healthy_servers = []
        for server_name, server in self.servers.items():
            if await self.check_server_health(server_name):
                healthy_servers.append(server)
        
        if not healthy_servers:
            return {"error": "没有可用的Nessus服务器"}
        
        # 分发任务
        tasks_per_server = len(targets) // len(healthy_servers)
        
        for i, server in enumerate(healthy_servers):
            start_idx = i * tasks_per_server
            end_idx = start_idx + tasks_per_server if i < len(healthy_servers) - 1 else len(targets)
            
            server_targets = targets[start_idx:end_idx]
            
            if server_targets:
                print(f"[*] 服务器 {i+1} 处理 {len(server_targets)} 个目标")
                
                for target in server_targets:
                    try:
                        result = await server.full_scan_workflow(target, f"分布式扫描 - {target}")
                        results[target] = result
                    except Exception as e:
                        print(f"[-] 扫描 {target} 失败: {e}")
                        results[target] = {"error": str(e)}
        
        return results

# 全局管理器实例
nessus_manager = NessusManager()

# 使用示例
async def test_enhanced_nessus_integration():
    """测试增强的Nessus集成"""
    # 测试多服务器管理器
    manager = NessusManager()
    
    print("🧪 测试Nessus服务器健康状态...")
    for server_name in manager.servers:
        health = await manager.check_server_health(server_name)
        print(f"服务器 {server_name}: {'✅ 健康' if health else '❌ 不可用'}")
    
    # 获取最佳服务器
    best_server = await manager.get_best_server()
    if best_server:
        print(f"[+] 选择的最佳服务器: {best_server}")
        
        # 测试扫描
        results = await best_server.full_scan_workflow("192.168.1.1", "增强测试扫描")
        print(f"扫描结果: {results}")
        
        if results['status'] == 'success':
            summary = best_server.generate_summary_report(results)
            print(summary)
    
    # 测试分布式扫描
    print("\n🧪 测试分布式扫描...")
    targets = ["192.168.1.1", "192.168.1.2", "192.168.1.3"]
    distributed_results = await manager.distributed_scan(targets)
    print(f"分布式扫描结果: {distributed_results}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_nessus_integration())