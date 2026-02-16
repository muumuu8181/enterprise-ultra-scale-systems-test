import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Card, Statistic, Row, Col } from 'antd';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import type { SPCChartData } from '../types';

interface SpcChartProps {
    parameter: string;
}

const SpcChart: React.FC<SpcChartProps> = ({ parameter }) => {
    const [chartData, setChartData] = useState<SPCChartData | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await axios.get<SPCChartData>(`http://localhost:8000/api/v1/spc/chart/${parameter}`);
                setChartData(response.data);
            } catch (error) {
                console.error("Error fetching SPC data:", error);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 5000); // Refresh data
        return () => clearInterval(interval);
    }, [parameter]);

    if (!chartData) return <div>Loading SPC Data...</div>;

    return (
        <Card title={`Xbar-R Chart: ${parameter.toUpperCase()}`}>
            <Row gutter={16} style={{ marginBottom: 20 }}>
                <Col span={8}>
                    <Statistic title="Cpk" value={chartData.cpk} precision={3} valueStyle={{ color: chartData.cpk < 1.33 ? '#cf1322' : '#3f8600' }} />
                </Col>
                <Col span={8}>
                    <Statistic title="USL" value={chartData.usl} />
                </Col>
                <Col span={8}>
                    <Statistic title="LSL" value={chartData.lsl} />
                </Col>
            </Row>

            <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                    <LineChart data={chartData.data}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="id" />
                        <YAxis domain={['auto', 'auto']} />
                        <Tooltip />
                        <Legend />
                        <ReferenceLine y={chartData.usl} label="USL" stroke="red" strokeDasharray="3 3" />
                        <ReferenceLine y={chartData.lsl} label="LSL" stroke="red" strokeDasharray="3 3" />
                        <Line type="monotone" dataKey="xbar" stroke="#8884d8" name="X-bar" />
                        <Line type="monotone" dataKey="ucl_x" stroke="#ff7300" dot={false} strokeDasharray="5 5" name="UCL" />
                        <Line type="monotone" dataKey="lcl_x" stroke="#ff7300" dot={false} strokeDasharray="5 5" name="LCL" />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </Card>
    );
};

export default SpcChart;
