FROM quay.io/centos/centos:7

# Fix repo source for EOL CentOS 7
RUN sed -i 's|mirrorlist=|#mirrorlist=|g' /etc/yum.repos.d/CentOS-Base.repo && \
    sed -i 's|#baseurl=|baseurl=|g' /etc/yum.repos.d/CentOS-Base.repo && \
    sed -i 's|http://mirror.centos.org|http://vault.centos.org|g' /etc/yum.repos.d/CentOS-Base.repo && \
    yum clean all && yum makecache

# Install Python 3.11
RUN yum install -y gcc gcc-c++ make wget zlib-devel bzip2 bzip2-devel \
    xz-devel libffi-devel readline-devel sqlite sqlite-devel tk-devel gdbm-devel \
 && cd /usr/src \
 && wget https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz \
 && tar xzf Python-3.11.9.tgz \
 && cd Python-3.11.9 \
 && ./configure --enable-optimizations --with-ensurepip=install \
 && make -j$(nproc) \
 && make altinstall \
 && ln -s /usr/local/bin/python3.11 /usr/bin/python3 \
 && ln -s /usr/local/bin/pip3.11 /usr/bin/pip3 \
 && cd /usr/src && rm -rf Python-3.11.9* \
 && yum clean all
 
# Install dependencies
RUN yum install -y java-1.8.0-openjdk tar wget python3 epel-release openssh-server openssh-clients passwd \
    && yum install -y python3-pip java-1.8.0-openjdk-devel sudo which git hostname net-tools \
    && yum clean all \
    && ssh-keygen -A

# Java symlink
#RUN ln -s /usr/lib/jvm/java-1.8.0-openjdk-1.8.0.412.b08-1.el7_9.x86_64/jre /usr/lib/jvm/java-1.8.0-openjdk

# Create hadoop user and workdir
RUN useradd -m -d /home/hadoop -s /bin/bash hadoop && \
    echo "hadoop:hadoop" | chpasswd && \
    mkdir -p /dxhouse && chown -R hadoop:hadoop /dxhouse  && \
    mkdir -p /home/hadoop/.ssh && \
    chown -R hadoop:hadoop /home/hadoop/.ssh

RUN echo "hadoop ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Enable SSH for Hadoop user
RUN ssh-keygen -A && \
    mkdir -p /home/hadoop/.ssh && \
    chown -R hadoop:hadoop /home/hadoop/.ssh

USER hadoop
WORKDIR /home/hadoop

# Generate SSH keys
RUN ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa && \
    cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys && \
    chmod 600 ~/.ssh/authorized_keys && chmod 700 ~/.ssh

# Set environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk \
    HADOOP_HOME=/dxhouse/hadoop \
    SPARK_HOME=/dxhouse/spark \
    HIVE_HOME=/dxhouse/hive \
    SQOOP_HOME=/dxhouse/sqoop \
    TEZ_HOME=/dxhouse/tez \
    HIVE_AUX_JARS_PATH=$TEZ_HOME/*:$HIVE_AUX_JARS_PATH \
    ICEBERG_HOME=/dxhouse/iceberg \
    PATH=$PATH:/dxhouse/hadoop/bin:/dxhouse/hadoop/sbin:/dxhouse/spark/bin:/dxhouse/spark/sbin:/dxhouse/hive/bin:/dxhouse/sqoop/bin:/dxhouse/tez/bin:/dxhouse/tez/conf \
    HDFS_NAMENODE_USER=hadoop \
    HDFS_DATANODE_USER=hadoop \
    HDFS_SECONDARYNAMENODE_USER=hadoop \
    YARN_RESOURCEMANAGER_USER=hadoop \
    YARN_NODEMANAGER_USER=hadoop \
    SPARK_SERIALIZER=org.apache.spark.serializer.JavaSerializer \
    HIVE_SPARK_SERIALIZER=java \
    SQOOP_VERSION=1.4.7

# Make environment variables available to all SSH/non-login shells
USER root
RUN bash -c "printenv | grep -E 'JAVA_HOME|HADOOP_HOME|SPARK_HOME|HIVE_HOME|SQOOP_HOME|TEZ_HOME|ICEBERG_HOME|PATH|HDFS_|YARN_' \
    | sed 's/^/export /' > /etc/profile.d/dxhouse.sh" && \
    chmod +x /etc/profile.d/dxhouse.sh
USER hadoop



# Hadoop
RUN wget https://downloads.apache.org/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz -P /dxhouse && \
    tar -xzf /dxhouse/hadoop-3.3.6.tar.gz -C /dxhouse && \
    mv /dxhouse/hadoop-3.3.6 /dxhouse/hadoop && rm -f /dxhouse/hadoop-3.3.6.tar.gz

# Spark
RUN wget https://archive.apache.org/dist/spark/spark-3.4.2/spark-3.4.2-bin-hadoop3.tgz -P /dxhouse && \
    tar -xzf /dxhouse/spark-3.4.2-bin-hadoop3.tgz -C /dxhouse && \
    mv /dxhouse/spark-3.4.2-bin-hadoop3 /dxhouse/spark && \
    rm -f /dxhouse/spark-3.4.2-bin-hadoop3.tgz

# Hive
RUN wget https://archive.apache.org/dist/hive/hive-3.1.3/apache-hive-3.1.3-bin.tar.gz -P /dxhouse && \
    tar -xzf /dxhouse/apache-hive-3.1.3-bin.tar.gz -C /dxhouse && \
    mv /dxhouse/apache-hive-3.1.3-bin /dxhouse/hive && \
    rm -f /dxhouse/apache-hive-3.1.3-bin.tar.gz

# Tez
RUN wget https://downloads.apache.org/tez/0.10.4/apache-tez-0.10.4-bin.tar.gz -P /dxhouse && \
    tar -xzf /dxhouse/apache-tez-0.10.4-bin.tar.gz -C /dxhouse && \
    mv /dxhouse/apache-tez-0.10.4-bin /dxhouse/tez && \
    rm -f /dxhouse/apache-tez-0.10.4-bin.tar.gz

# Sqoop
RUN wget https://archive.apache.org/dist/sqoop/1.4.7/sqoop-1.4.7.bin__hadoop-2.6.0.tar.gz -P /tmp && \
    tar -xzf /tmp/sqoop-1.4.7.bin__hadoop-2.6.0.tar.gz -C /dxhouse && \
    mv /dxhouse/sqoop-1.4.7.bin__hadoop-2.6.0 $SQOOP_HOME && \
    rm -f /tmp/sqoop-1.4.7.bin__hadoop-2.6.0.tar.gz && \
    rm -rf $SQOOP_HOME/lib/hadoop* && \
    rm -rf $SQOOP_HOME/lib/jdiff $SQOOP_HOME/lib/lib $SQOOP_HOME/lib/sources $SQOOP_HOME/lib/webapps && \
    mkdir -p $SQOOP_HOME/lib && \
    for dir in $HADOOP_HOME/share/hadoop/common/* \
               $HADOOP_HOME/share/hadoop/hdfs/* \
               $HADOOP_HOME/share/hadoop/mapreduce/* \
               $HADOOP_HOME/share/hadoop/yarn/*; do \
        ln -sf "$dir" $SQOOP_HOME/lib/; \
    done 

# MySQL connector for Hive
RUN wget https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/8.0.33/mysql-connector-j-8.0.33.jar \
    -P /dxhouse/hive/lib

# MySQL Connector for SQOOP
RUN cp /dxhouse/hive/lib/mysql-connector-j-8.0.33.jar /dxhouse/sqoop/lib/
RUN cp /dxhouse/hive/lib/mysql-connector-j-8.0.33.jar /dxhouse/spark/jars/

# Add Apache Commons Lang
RUN wget https://archive.apache.org/dist/commons/lang/binaries/commons-lang-2.6-bin.tar.gz -P /tmp && \
    tar -xzf /tmp/commons-lang-2.6-bin.tar.gz -C /tmp && \
    cp /tmp/commons-lang-2.6/commons-lang-2.6.jar /dxhouse/sqoop/lib/ && \
    rm -rf /tmp/commons-lang-2.6*

# Add Apache Commons Collections for Hive/Spark integration
RUN wget https://repo1.maven.org/maven2/commons-collections/commons-collections/3.2.2/commons-collections-3.2.2.jar \
    -P /dxhouse/hive/lib && \
    cp /dxhouse/hive/lib/commons-collections-3.2.2.jar /dxhouse/spark/jars/ && \
    cp /dxhouse/hive/lib/commons-collections-3.2.2.jar /dxhouse/sqoop/lib/

# Add Apache Iceberg Spark Runtime
# RUN mkdir -p /dxhouse/iceberg && \
#     wget https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.4_2.12/1.7.2/iceberg-spark-runtime-3.4_2.12-1.7.2.jar \
#     -P /dxhouse/iceberg
RUN mkdir -p /dxhouse/iceberg && \
    wget https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.4_2.12/1.3.1/iceberg-spark-runtime-3.4_2.12-1.3.1.jar \
    -P /dxhouse/iceberg

# Add Apache Iceberg Hive Runtime
# RUN wget https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-hive-runtime/1.7.2/iceberg-hive-runtime-1.7.2.jar \
#     -P /dxhouse/hive/lib
RUN wget https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-hive-runtime/1.3.1/iceberg-hive-runtime-1.3.1.jar \
    -P /dxhouse/hive/lib

# Add Java home to Hadoop config
RUN echo 'export JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk' >> /dxhouse/hadoop/etc/hadoop/hadoop-env.sh

# # Tez jars in Hive auxlib path
# RUN mkdir -p /dxhouse/hive/auxlib && \
#     cp /dxhouse/tez/*.jar /dxhouse/hive/auxlib/ && \
#     cp /dxhouse/tez/lib/*.jar /dxhouse/hive/auxlib/ 

# Download Hive-on-Spark assembly JAR
RUN wget https://repo1.maven.org/maven2/org/apache/hive/hive-spark-client/3.1.3/hive-spark-client-3.1.3.jar \
    -P /dxhouse/hive/lib/

RUN chmod 775 /dxhouse/hive/lib/hive-spark-client-3.1.3.jar
RUN cp /dxhouse/hive/lib/hive-spark-client-3.1.3.jar /dxhouse/spark/jars/

# # Also ensure the Spark JARs are accessible to Hive
# RUN for jar in /dxhouse/spark/jars/*.jar; do \
#         jarname=$(basename "$jar"); \
#         # Skip JARs that end with version patterns that might conflict \
#         if [[ ! "$jarname" =~ -2\.3\.9\.jar$ ]] && \
#            [[ ! "$jarname" =~ hive-exec ]] && \
#            [[ ! "$jarname" =~ hive-metastore ]] && \
#            [[ ! "$jarname" =~ hive-cli ]] && \
#            [[ ! "$jarname" =~ slf4j-log4j12 ]] && \
#            [[ ! -f "/dxhouse/hive/lib/$jarname" ]]; then \
#             ln -sf "$jar" "/dxhouse/hive/lib/$jarname"; \
#         fi \
#     done

# # Remove any broken symbolic links
# RUN find /dxhouse/hive/lib -type l ! -exec test -e {} \; -delete

# Copy configs
COPY config/hadoop/* /dxhouse/hadoop/etc/hadoop/
COPY config/hive/* /dxhouse/hive/conf/
COPY config/spark/* /dxhouse/spark/conf/
COPY config/hive/* /dxhouse/spark/conf/
COPY config/tez/tez-site.xml /dxhouse/tez/conf/


EXPOSE 22 9870 9864 8088 8042 7077 8080 10000 10002 9600 16000

USER root
# Copy entrypoint script
COPY config/*.sh /dxhouse/bin/
RUN chmod +x /dxhouse/bin/*
RUN mkdir /dxhouse/logs
RUN chmod 777 /dxhouse/logs
RUN mkdir /dxhouse/logs/hive
RUN chmod 777 /dxhouse/logs/hive
RUN mkdir /dxhouse/logs/spark
RUN chmod 777 /dxhouse/logs/spark

CMD ["/bin/bash"]
CMD ["/usr/sbin/sshd", "-D"]
