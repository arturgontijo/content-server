const RegistryAbi = [{"anonymous":false,"inputs":[{"indexed":true,"name":"orgId","type":"bytes32"}],"name":"OrganizationCreated","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"orgId","type":"bytes32"}],"name":"OrganizationModified","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"orgId","type":"bytes32"}],"name":"OrganizationDeleted","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"orgId","type":"bytes32"},{"indexed":true,"name":"serviceId","type":"bytes32"},{"indexed":false,"name":"metadataURI","type":"bytes"}],"name":"ServiceCreated","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"orgId","type":"bytes32"},{"indexed":true,"name":"serviceId","type":"bytes32"},{"indexed":false,"name":"metadataURI","type":"bytes"}],"name":"ServiceMetadataModified","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"orgId","type":"bytes32"},{"indexed":true,"name":"serviceId","type":"bytes32"}],"name":"ServiceTagsModified","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"orgId","type":"bytes32"},{"indexed":true,"name":"serviceId","type":"bytes32"}],"name":"ServiceDeleted","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"orgId","type":"bytes32"},{"indexed":true,"name":"typeRepositoryId","type":"bytes32"}],"name":"TypeRepositoryCreated","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"orgId","type":"bytes32"},{"indexed":true,"name":"typeRepositoryId","type":"bytes32"}],"name":"TypeRepositoryModified","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"orgId","type":"bytes32"},{"indexed":true,"name":"typeRepositoryId","type":"bytes32"}],"name":"TypeRepositoryDeleted","type":"event"},{"constant":false,"inputs":[{"name":"orgId","type":"bytes32"},{"name":"orgName","type":"string"},{"name":"members","type":"address[]"}],"name":"createOrganization","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"orgId","type":"bytes32"},{"name":"newOwner","type":"address"}],"name":"changeOrganizationOwner","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"orgId","type":"bytes32"},{"name":"orgName","type":"string"}],"name":"changeOrganizationName","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"orgId","type":"bytes32"},{"name":"newMembers","type":"address[]"}],"name":"addOrganizationMembers","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"orgId","type":"bytes32"},{"name":"existingMembers","type":"address[]"}],"name":"removeOrganizationMembers","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"orgId","type":"bytes32"}],"name":"deleteOrganization","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"orgId","type":"bytes32"},{"name":"serviceId","type":"bytes32"},{"name":"metadataURI","type":"bytes"},{"name":"tags","type":"bytes32[]"}],"name":"createServiceRegistration","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"orgId","type":"bytes32"},{"name":"serviceId","type":"bytes32"},{"name":"metadataURI","type":"bytes"}],"name":"updateServiceRegistration","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"orgId","type":"bytes32"},{"name":"serviceId","type":"bytes32"},{"name":"tags","type":"bytes32[]"}],"name":"addTagsToServiceRegistration","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"orgId","type":"bytes32"},{"name":"serviceId","type":"bytes32"},{"name":"tags","type":"bytes32[]"}],"name":"removeTagsFromServiceRegistration","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"orgId","type":"bytes32"},{"name":"serviceId","type":"bytes32"}],"name":"deleteServiceRegistration","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"orgId","type":"bytes32"},{"name":"repositoryId","type":"bytes32"},{"name":"repositoryURI","type":"bytes"},{"name":"tags","type":"bytes32[]"}],"name":"createTypeRepositoryRegistration","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"orgId","type":"bytes32"},{"name":"repositoryId","type":"bytes32"},{"name":"repositoryURI","type":"bytes"}],"name":"updateTypeRepositoryRegistration","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"orgId","type":"bytes32"},{"name":"repositoryId","type":"bytes32"},{"name":"tags","type":"bytes32[]"}],"name":"addTagsToTypeRepositoryRegistration","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"orgId","type":"bytes32"},{"name":"repositoryId","type":"bytes32"},{"name":"tags","type":"bytes32[]"}],"name":"removeTagsFromTypeRepositoryRegistration","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"orgId","type":"bytes32"},{"name":"repositoryId","type":"bytes32"}],"name":"deleteTypeRepositoryRegistration","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"listOrganizations","outputs":[{"name":"orgIds","type":"bytes32[]"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"orgId","type":"bytes32"}],"name":"getOrganizationById","outputs":[{"name":"found","type":"bool"},{"name":"id","type":"bytes32"},{"name":"name","type":"string"},{"name":"owner","type":"address"},{"name":"members","type":"address[]"},{"name":"serviceIds","type":"bytes32[]"},{"name":"repositoryIds","type":"bytes32[]"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"orgId","type":"bytes32"}],"name":"listServicesForOrganization","outputs":[{"name":"found","type":"bool"},{"name":"serviceIds","type":"bytes32[]"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"orgId","type":"bytes32"},{"name":"serviceId","type":"bytes32"}],"name":"getServiceRegistrationById","outputs":[{"name":"found","type":"bool"},{"name":"id","type":"bytes32"},{"name":"metadataURI","type":"bytes"},{"name":"tags","type":"bytes32[]"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"orgId","type":"bytes32"}],"name":"listTypeRepositoriesForOrganization","outputs":[{"name":"found","type":"bool"},{"name":"repositoryIds","type":"bytes32[]"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"orgId","type":"bytes32"},{"name":"repositoryId","type":"bytes32"}],"name":"getTypeRepositoryById","outputs":[{"name":"found","type":"bool"},{"name":"id","type":"bytes32"},{"name":"repositoryURI","type":"bytes"},{"name":"tags","type":"bytes32[]"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"listServiceTags","outputs":[{"name":"tags","type":"bytes32[]"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"tag","type":"bytes32"}],"name":"listServicesForTag","outputs":[{"name":"orgIds","type":"bytes32[]"},{"name":"serviceIds","type":"bytes32[]"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"listTypeRepositoryTags","outputs":[{"name":"tags","type":"bytes32[]"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"tag","type":"bytes32"}],"name":"listTypeRepositoriesForTag","outputs":[{"name":"orgIds","type":"bytes32[]"},{"name":"repositoryIds","type":"bytes32[]"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"interfaceID","type":"bytes4"}],"name":"supportsInterface","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"view","type":"function"}]