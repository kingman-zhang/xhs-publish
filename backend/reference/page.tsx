'use client';
import { useState, useEffect } from 'react';
import React from 'react';
import { Button, Flex, Typography,Input,Image } from 'antd';
import Script from 'next/script';
import { useParams } from 'next/navigation';
const { Text } = Typography;

interface XhsShareConfig {
    appKey: string;
    nonce: string;
    timeStamp: number;
    signature: string;
}

interface TaskData {
    topics: string[];
    summary: string;
    banner_url: string;
    content_urls: string[];
    title: string;
    top_comment: string;
}


export default function XhsTask() {
    const params = useParams();
    const taskid = params.taskid as string;

    const [xhsShareConfig, setXhsShareConfig] = useState<XhsShareConfig | null>(null);
    const [taskData, setTaskData] = useState<TaskData | null>(null);
    const [loading, setLoading] = useState(false);

    // 获取小红书分享的配置
    useEffect(() => {
        const fetchConfig = async () => {
            try {
                const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/xhs/share_verify_config`);
                const data = await response.json();
                if (data.status === 'success') {
                    setXhsShareConfig(data.data);
                }
            } catch (error) {
                console.error('获取配置失败:', error);
            }
        };

        fetchConfig();
    }, []);

    // 获取笔记详情
    useEffect(() => {
        const fetchTaskData = async () => {
            try {
                const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/task/note/${taskid}`);
                const data = await response.json();
                if (data.status === 'success') {
                    setTaskData(data.data);
                }
            } catch (error) {
                console.error('获取任务数据失败:', error);
            }
        };

        fetchTaskData();
    }, [taskid]); // 添加 taskid 到依赖数组

    let combinedContent = '';
    let images: string[] = [] // 使用具体的字符串数组类型
    if (taskData) {
        const { topics, summary, banner_url, content_urls } = taskData;
        combinedContent = `${summary} ${topics.map(item => `#${item}`).join(' ')}`;
        images = [banner_url, ...content_urls];
    }

    const baseStyle: React.CSSProperties = {
        width: '100%'
    };
    const itemStyle: React.CSSProperties = {
        width: '80%'
    };
    const { TextArea } = Input;

    const handleShare = async () => {
        if (loading || !taskData || !xhsShareConfig) return; // 添加空值检查
        setLoading(true);


        try {
            // @ts-expect-error 小红书 SDK 类型未定义
            await window.xhs.share({
                shareInfo: {
                    type: 'normal',
                    title: taskData.title,
                    content: combinedContent,
                    images: images,
                    cover: taskData.banner_url
                },
                verifyConfig: {
                    appKey: xhsShareConfig.appKey,
                    nonce: xhsShareConfig.nonce,
                    timestamp: xhsShareConfig.timeStamp.toString(),
                    signature: xhsShareConfig.signature,
                },
                fail: (e: Error) => {
                    console.log('分享失败:', e);
                },
            });
        } catch (error) {
            console.error('分享出错:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <Script
                src="https://fe-static.xhscdn.com/biz-static/goten/xhs-1.0.1.js"
                strategy="afterInteractive"
                onLoad={() => {
                    console.log('小红书分享脚本加载完成');
                }}
            />
            <Flex vertical justify='center' align='center' gap={16} style={baseStyle}>
                {taskData && (
                    <>
                        <div style={itemStyle}>
                            <Typography.Title level={5}>标题：</Typography.Title>
                            <Input
                                count={{
                                    show: true,
                                    max: 20,
                                }}
                                defaultValue={taskData.title}
                                disabled={true} 
                            />
                        </div>
                        <div style={itemStyle}>
                            <Typography.Title level={5}>图片</Typography.Title>
                            <Image.PreviewGroup
                                preview={{
                                onChange: (current, prev) => console.log(`current index: ${current}, prev index: ${prev}`),
                                }}
                            >
                                {images.map((image, index) => (
                                    <span key={index}>
                                        <Image width={80} src={image} alt={`Image ${index}`} />
                                    </span>
                                ))}
                               
                            </Image.PreviewGroup>
                        </div>
                        <div style={itemStyle}>
                            <Typography.Title level={5}>内容</Typography.Title>
                            <TextArea 
                            count={{
                                show: true,
                                max: 1000,
                            }}
                            rows={20} 
                            value={combinedContent} 
                            disabled={true} 
                             />
                        </div>
                        <div style={itemStyle}>
                            <Typography.Title level={5}>置顶评论</Typography.Title>
                            <TextArea 
                            rows={2} 
                            value={taskData.top_comment} 
                            disabled={true} 
                             />
                             <Text copyable={{ text: taskData.top_comment }} />
                        </div>
                        <div style={itemStyle}>
                            <Button 
                                type="primary" 
                                size='large' 
                                onClick={handleShare}
                                loading={loading}
                                disabled={loading}
                            >
                                分享到小红书
                            </Button>
                        </div>
                    </>
                )}
            </Flex>
        </>
    );


}

