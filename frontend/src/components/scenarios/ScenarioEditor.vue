<template>
  <div class="main">
		<div class="columns">
      <div class="column is-1 toolbox">
        <ToolBox :currentTool="currentTool" @currentToolChange="onCurrentToolChange">
        </ToolBox>
        <hr/>
        <h5 class="title is-5 has-text-centered">Backup / Restore</h5>
        <a class="button is-small is-fullwidth" :href="backupURL" download="scenario_backup.json">Backup</a>
        <a class="button is-small is-fullwidth" href="#">Restore</a>
      </div>

			<svg ref="svg" class="column workspace" width="100%" height="700" @click="onMainSVGClick" @mousemove="onMouseMove">

				<NetworkLink v-for="el in links" :key="el.gid" :el="el" @click="onLinkClick"></NetworkLink>
				<NetworkNode v-for="el in networks" :key="el.gid" :el="el" @click="onNetworkClick"></NetworkNode>
				<Instance v-for="el in instances" :key="el.gid" :el="el" @click="onInstanceClick"></Instance>
				<Router v-for="el in routers" :key="el.gid" :el="el" @click="onRouterClick"></Router>
				<TempLink v-if="tempLink !== null" :tempLink="tempLink"></TempLink>
			</svg>

			<div class="column is-2 property">
				<PropertiesEditor :el="selectedElement" :instanceConfigurations="instanceConfigurations" :routerConfigurations="routerConfigurations" :flavors="flavors" @delete="onDeleteElement($event)"></PropertiesEditor>
			</div>
		</div>

    <div class="center">
      <div class="field">
        <label class="label">Name</label>
        <p class="control">
          <input class="input" type="text" placeholder="Scenario name" v-model="name">
        </p>
      </div>
      <div class="field">
        <label class="label">Description</label>
        <p class="control">
          <textarea class="textarea" placeholder="Scenario's description" v-model="description"></textarea>
        </p>
      </div>
      <div class="field">
        <label class="label">Publicly available</label>
        <p class="control">
          <label class="radio">
            <input type="radio" value=true v-model="isPublic"> Yes
          </label>
          <label class="radio">
            <input type="radio" value=false v-model="isPublic"> No
          </label>
        </p>
      </div>
      <div class="field">
        <button v-if="isPublishing" type="submit" class="button is-primary is-loading">Publish</button>
        <button v-else-if="isNewScenario" type="submit" @click="onPublishBtn" class="button is-primary">Publish</button>
        <button v-else type="submit" @click="onPublishBtn" class="button is-primary">Update</button>
        <p v-if="error" class="is-danger">{{error}}</p>
      </div>
    </div>
  </div>
</template>

<script>
import PropertiesEditor from '@/components/scenarios/PropertiesEditor.vue'
import ToolBox from '@/components/scenarios/ToolBox.vue'

import Instance from '@/components/networkelements/Instance.vue'
import Router from '@/components/networkelements/Router.vue'
import NetworkNode from '@/components/networkelements/Network.vue'
import NetworkLink from '@/components/networkelements/Link.vue'
import TempLink from '@/components/networkelements/TempLink.vue'

import {
  PATCHscenario, 
  POSTscenario, 
  GETscenario, 
  LISTInstanceConfigurations, 
  LISTRouterConfigurations,
  LISTFlavors
} from '@/api'

const uuidv1 = require('uuid/v1')

export default {
  name: "ScenarioEditor",
  components: {
    ToolBox,
    PropertiesEditor,

    Instance,
		Router,
    NetworkNode,
    NetworkLink,
    TempLink,
  },
  data: function () {
    return {
      name: null,
      description: null,

			topo: null,

      isPublic: false,
      isPublishing: false,
			isNewScenario: false,


      error: null,

      currentTool: 'select',
      selectedElement: null, // the element is selected on the screen using select tool
      tempLink: null,

			networks: [],
			instances: [],
			routers: [],
			links: [],

      instanceConfigurations: [],
      routerConfigurations: [],

      flavors: []
    }
  },

  beforeRouteEnter: function (to, from, next) {
		if (to.name === "ScenarioEditor") {
			GETscenario(to.params.id, json => {
				next(vm => vm.setData(json))
			})
		} else {
			next()
		}
  },

	created: function () {
		switch (this.$route.name) {
			case "ScenarioEditor":
				this.isNewScenario = false
				break
			case "NewScenario":
				this.isNewScenario = true
				break
		}

    LISTInstanceConfigurations(json => {
      this.instanceConfigurations = json
    })

    LISTRouterConfigurations(json => {
      this.routerConfigurations = json
    })

    LISTFlavors(json => {
      this.flavors = json
    })
	},

  computed: {
    backupURL: function () {
      let topo = {
        networks: this.networks,
        routers: this.routers,
        instances: this.instances,
        links: this.links,
      }
      let json = JSON.stringify(topo)
      let blob = new Blob([json], {type: "application/json"})
      return URL.createObjectURL(blob)
    }
  },

  methods: {
    setData: function (json) {
      this.name = json.name
      this.description = json.description
      this.isPublic = json.isPublic

			if (json.topo.hasOwnProperty('instances'))
      	this.instances = json.topo.instances

			if (json.topo.hasOwnProperty('networks'))
      	this.networks = json.topo.networks

			if (json.topo.hasOwnProperty('routers'))
				this.routers = json.topo.routers

			if (json.topo.hasOwnProperty('links'))
				this.links = json.topo.links
    },

		/**
		 * Event handler when user select a new tool in ToolBox
		 */
    onCurrentToolChange: function (newTool) {
      this.currentTool = newTool
      this.tempLink = null
    },

		/**
		 * Event handler when user delete a network component from the topo designer
		 */
    onDeleteElement: function (elId) {
      switch (this.selectedElement.type) {
        case 'NetworkLink': {
					this.links = this.links.filter(el => {
						return el.gid !== elId
					})
          break
        }
        case 'NetworkNode': {
          this.networks = this.networks.filter(el => {
            return el.gid !== elId
          })
					this.links = this.links.filter(el => {
            return ! (el.network.gid === elId)
					})
          break
        }
        case 'Instance': {
          this.instances = this.instances.filter(el => {
            return el.gid !== elId
          })
					this.links = this.links.filter(el => {
						return el.target.gid !== elId
					})
          break
        }
				case 'Router': {
					this.routers = this.routers.filter(el => {
						return el.gid !== elId
					})
					this.links = this.links.filter(el => {
						return el.target.gid !== elId
					})
				}
        case 'default': {
          break
        }
      }
      this.selectedElement = null
    },

		/**
		 * Event handler when main svg is clicked.
		 */
    onMainSVGClick: function (e) {
      let svg = this.$refs.svg
      let pt = svg.createSVGPoint()
      pt.x = e.clientX
      pt.y = e.clientY
      let realPt = pt.matrixTransform(svg.getScreenCTM().inverse())

      switch (this.currentTool) {
        case 'network':
          {
            let newNetwork = {
							gid: uuidv1(),
              type: 'NetworkNode',
              name: 'Network' + this.networks.length,
              x: realPt.x,
              y: realPt.y,
              cidr: null
            }
            this.networks.push(newNetwork)
            break
          }
        case 'instance':
          {
            let newInstance = {
							gid: uuidv1(),
              type: 'Instance',
              name: 'Instance' + this.instances.length,
              x: realPt.x,
              y: realPt.y,
              image: null,
              status: null,
              configurations: []
            }
            this.instances.push(newInstance)
            break
          }
        case 'router':
          {
            let newRouter = {
              gid: uuidv1(),
              type: 'Router',
              name: 'Router' + this.routers.length,
              x: realPt.x,
              y: realPt.y,
              status: null,
              configurations: []
            }
            this.routers.push(newRouter)
            break
          }
      }
    },

    onMouseMove: function (e) {
      let svg = this.$refs.svg
      let pt = svg.createSVGPoint()
      pt.x = e.clientX
      pt.y = e.clientY

      let realPt = pt.matrixTransform(svg.getScreenCTM().inverse())

      if (this.tempLink !== null) {
        let deltaX = 5
        let deltaY = 5
        if (realPt.x < this.tempLink.x1) {
          deltaX = -5
        }
        if (realPt.y < this.tempLink.y1) {
          deltaY = -5
        }
        this.tempLink.x2 = realPt.x - deltaX // to prevent the templine become clickable
        this.tempLink.y2 = realPt.y - deltaY // to prevent the templine become clickable
      }
    },

    onNetworkClick: function(element) {
			switch (this.currentTool) {
				case 'select':
        	this.selectedElement = element
					break
				case 'link':	
					if (this.tempLink === null) {
						this.tempLink = {
							network: element,
							x1: element.x,
							y1: element.y,
							x2: element.x,
							y2: element.y,
							target: null
						}
					} else {
						// a link is drawn from an instance or router
						if (this.tempLink.network === null) {
							let network = element
							let target = this.tempLink.target
							let newLink = {
								gid: uuidv1(),
								name: `${network.name}_${target.name}`,
								type: 'NetworkLink',
								network: network,
								target: target,
								ip: null
							}
							if (this.links.find(el => el.network == network && el.target == target) === undefined) { // not duplicated link)
									this.links.push(newLink)
									this.tempLink = null
							}
						}
					}
				break
			}
    },

    onRouterClick: function(element) {
      switch (this.currentTool) {
        case 'select': {
          this.selectedElement = element
          break;
        }
        case 'link': {
					if (this.tempLink === null){
						this.tempLink = {
							network: null,
							target: element,
							x1: element.x,
							y1: element.y,
							x2: element.x,
							y2: element.y
						}
					} else {
						if (this.tempLink.target === null) {
							let network = this.tempLink.network
							let target = element
							let newLink = {
								gid: uuidv1(),
								name: `${network.name}_${target.name}`,
								type: 'NetworkLink',
								network: network,
								target: target,
								ip: null
							}
							if (this.links.find(el => el.network == network && el.target == target) === undefined) { // not duplicated link)
									this.links.push(newLink)
									this.tempLink = null
							}
						}
					}
          break;
        }
      }
    },

    onInstanceClick: function(element) {
			switch (this.currentTool) {
				case 'select':
        	this.selectedElement = element
					break
				case 'link':
					if (this.tempLink === null){
						this.tempLink = {
							network: null,
							target: element,
							x1: element.x,
							y1: element.y,
							x2: element.x,
							y2: element.y
						}
					} else {
						if (this.tempLink.target === null) {
							let network = this.tempLink.network
							let target = element
							let newLink = {
								name: `${network.name}_${target.name}`,
								gid: uuidv1(),
								type: 'NetworkLink',
								network: network,
								target: target,
								ip: null
							}
							if (this.links.find(el => el.network == network && el.target == target) === undefined) { // not duplicated link)
									this.links.push(newLink)
									this.tempLink = null
							}
						}
					}
				break
			}
    },

    onLinkClick: function(element) {
      if (this.currentTool == 'select') {
				// Set selectedElement to the clicked link
        this.selectedElement = element
      }
    },

		/**
		 * Event handler when publish btn is clicked
		 */
    onPublishBtn: function () {
      this.error = null
      this.isPublishing = true
			let topo = {
				networks: this.networks,
				instances: this.instances,
				routers: this.routers,
				links: this.links
			}
			if (this.isNewScenario) {
				POSTscenario(this.name, this.description, this.isPublic, topo, json => {
					this.$router.push('/scenarios/')
				})
			} else {
				PATCHscenario(this.name, this.description, this.isPublic, topo, this.$route.params.id, json => {
					this.$router.push('/scenarios/')
				})
			}
    },
  }
}
</script>

<style scoped>
.main {
  margin-top: 20px;
}

.center {
  width: 60%;
  margin: auto;
}

.property {
  background-color: #f6f6f6;
  margin-left: 5px;
  margin-bottom: 5px;
}

.workspace {
  background-color: #f6f6f6;
  margin-bottom: 5px;
  width: 800px;
}

.toolbox {
  background-color: #f6f6f6;
  margin-right: 5px;
  margin-bottom: 5px;
}
</style>