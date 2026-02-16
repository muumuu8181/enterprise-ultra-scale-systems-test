import React from 'react';
import { Layout, Typography, Row, Col } from 'antd';
import FabOverview from './components/FabOverview';
import LotList from './components/LotList';
import SpcChart from './components/SpcChart';

const { Header, Content } = Layout;
const { Title } = Typography;

const App: React.FC = () => {
    return (
        <Layout style={{ minHeight: '100vh' }}>
            <Header style={{ backgroundColor: '#001529', display: 'flex', alignItems: 'center' }}>
                <Title level={3} style={{ color: 'white', margin: 0 }}>Semiconductor MES</Title>
            </Header>
            <Content style={{ padding: '24px' }}>
                <Row gutter={[16, 16]}>
                    <Col xs={24} lg={12}>
                        <FabOverview />
                    </Col>
                    <Col xs={24} lg={12}>
                        <LotList />
                    </Col>
                </Row>
                <Row gutter={[16, 16]} style={{ marginTop: '24px' }}>
                    <Col xs={24} lg={12}>
                        <SpcChart parameter="temp" />
                    </Col>
                    <Col xs={24} lg={12}>
                        <SpcChart parameter="pressure" />
                    </Col>
                </Row>
            </Content>
        </Layout>
    );
};

export default App;
